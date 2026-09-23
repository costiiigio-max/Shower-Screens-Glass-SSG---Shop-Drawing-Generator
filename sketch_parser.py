# sketch_parser.py
import os
import pickle
import base64
import json
import cv2
import numpy as np
import easyocr
import requests
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Tuple
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDRegressor

# Global Base OCR initialization
base_ocr = easyocr.Reader(['en'], gpu=False)


@dataclass
class HardwareCutout:
    cutout_type: str  # e.g., 'hinge_top', 'hinge_bottom', 'hinge_mid'
    x_offset_mm: float
    y_offset_mm: float


@dataclass
class ParsedGlassPanel:
    panel_id: int
    width_mm: float
    height_mm: float
    glass_type: str = "10mm Clear Toughened"
    cutouts: List[HardwareCutout] = field(default_factory=list)

    @property
    def area_m2(self) -> float:
        return (self.width_mm / 1000.0) * (self.height_mm / 1000.0)

    @property
    def weight_kg(self) -> float:
        return self.area_m2 * 25.0  # ~25kg per m2 for 10mm glass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "area_m2": round(self.area_m2, 3),
            "weight_kg": round(self.weight_kg, 2),
            "glass_type": self.glass_type,
            "cutouts": [asdict(c) for c in self.cutouts]
        }


class OnlineHardwareModel:
    """Self-learning regression model that remembers hardware placement offsets."""

    def __init__(self, model_path: str = "hardware_model.pkl"):
        self.model_path = model_path
        self.top_hinge_model = SGDRegressor(learning_rate="constant", eta0=0.01)
        self.bottom_hinge_model = SGDRegressor(learning_rate="constant", eta0=0.01)
        self._bootstrap_or_load()

    def _bootstrap_or_load(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                saved = pickle.load(f)
                self.top_hinge_model = saved["top"]
                self.bottom_hinge_model = saved["bottom"]
        else:
            X_baseline = np.array([
                [1800.0, 800.0, 25.0],
                [2000.0, 900.0, 30.0],
                [2100.0, 900.0, 31.5],
                [2400.0, 1000.0, 45.0]
            ])
            y_baseline = np.array([250.0, 250.0, 250.0, 250.0])
            self.top_hinge_model.fit(X_baseline, y_baseline)
            self.bottom_hinge_model.fit(X_baseline, y_baseline)
            self.save_state()

    def save_state(self):
        with open(self.model_path, "wb") as f:
            pickle.dump({"top": self.top_hinge_model, "bottom": self.bottom_hinge_model}, f)

    def predict_offsets(self, height_mm: float, width_mm: float, weight_kg: float) -> Tuple[float, float]:
        X = np.array([[height_mm, width_mm, weight_kg]])
        pred_top = self.top_hinge_model.predict(X)[0]
        pred_bot = self.bottom_hinge_model.predict(X)[0]
        return max(50.0, float(pred_top)), max(50.0, float(pred_bot))

    def learn(self, height_mm: float, width_mm: float, weight_kg: float, actual_top_mm: float, actual_bot_mm: float):
        X = np.array([[height_mm, width_mm, weight_kg]])
        self.top_hinge_model.partial_fit(X, [actual_top_mm])
        self.bottom_hinge_model.partial_fit(X, [actual_bot_mm])
        self.save_state()


class SketchStyleMemoryEngine:
    """Local visual feature memory that stores handwriting styles and custom symbols."""

    def __init__(self, memory_path: str = "sketch_memory.pkl"):
        self.memory_path = memory_path
        self.scaler = StandardScaler()
        self.knn = KNeighborsClassifier(n_neighbors=1, weights="distance")
        self.is_trained = False
        self._load()

    def _extract_features(self, img_crop: np.ndarray) -> np.ndarray:
        resized = cv2.resize(img_crop, (32, 32))
        if len(resized.shape) == 3:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        return resized.flatten() / 255.0

    def _load(self):
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "rb") as f:
                data = pickle.load(f)
                self.knn = data["knn"]
                self.scaler = data["scaler"]
                self.is_trained = data["is_trained"]

    def save_memory(self):
        with open(self.memory_path, "wb") as f:
            pickle.dump({"knn": self.knn, "scaler": self.scaler, "is_trained": self.is_trained}, f)

    def predict_symbol(self, img_crop: np.ndarray) -> Tuple[str, float]:
        if not self.is_trained or img_crop.size == 0:
            return "", 0.0
        features = self._extract_features(img_crop).reshape(1, -1)
        scaled = self.scaler.transform(features)
        pred = self.knn.predict(scaled)[0]
        distances, _ = self.knn.kneighbors(scaled)
        conf = 1.0 / (1.0 + float(distances[0][0]))
        return str(pred), conf

    def train_symbol(self, img_crop: np.ndarray, correct_label: str):
        features = self._extract_features(img_crop).reshape(1, -1)
        if not self.is_trained:
            self.scaler.fit(features)
            scaled = self.scaler.transform(features)
            self.knn.fit(scaled, [correct_label])
            self.is_trained = True
        else:
            scaled = self.scaler.transform(features)
            X_curr = self.knn._fit_X
            y_curr = self.knn._y
            self.knn.fit(np.vstack([X_curr, scaled]), np.append(y_curr, correct_label))
        self.save_memory()


class HybridSketchEngine:
    """Main Orchestrator executing Local Vision, VLLM Fallback, and ML Hardware Logic."""

    def __init__(self, openai_api_key: str = None):
        self.style_memory = SketchStyleMemoryEngine()
        self.hardware_ml = OnlineHardwareModel()
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

    def auto_place_hardware(self, width_mm: float, height_mm: float) -> List[HardwareCutout]:
        weight_kg = ((width_mm / 1000.0) * (height_mm / 1000.0)) * 25.0
        top_offset, bot_offset = self.hardware_ml.predict_offsets(height_mm, width_mm, weight_kg)

        cutouts = [
            HardwareCutout("hinge_top", x_offset_mm=0.0, y_offset_mm=top_offset),
            HardwareCutout("hinge_bottom", x_offset_mm=0.0, y_offset_mm=height_mm - bot_offset)
        ]
        if weight_kg > 35.0 or height_mm > 2100.0:
            cutouts.append(HardwareCutout("hinge_mid", x_offset_mm=0.0, y_offset_mm=height_mm / 2.0))
        return cutouts

    def parse_with_vllm(self, image_bytes: bytes) -> Dict[str, float]:
        """Queries Vision LLM for complex/messy sketches."""
        if not self.api_key:
            return {"width_mm": 900.0, "height_mm": 2000.0}

        base64_img = base64.b64encode(image_bytes).decode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are a glazier assistant. Read this hand-drawn shower screen sketch. "
                                "Extract the main glass panel width and height in millimeters. "
                                "Return STRICTLY valid JSON with keys: 'width_mm' and 'height_mm'."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
                        }
                    ]
                }
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 150
        }

        try:
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
            data = res.json()
            content = json.loads(data["choices"][0]["message"]["content"])
            return {
                "width_mm": float(content.get("width_mm", 900.0)),
                "height_mm": float(content.get("height_mm", 2000.0))
            }
        except Exception:
            return {"width_mm": 900.0, "height_mm": 2000.0}

    def process_sketch(self, image_bytes: bytes) -> Tuple[ParsedGlassPanel, str, List[Dict[str, Any]]]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        results = base_ocr.readtext(img)
        numbers = []
        crops_for_training = []
        high_confidence_matches = 0

        for (bbox, text, prob) in results:
            clean_num = ''.join(c for c in text if c.isdigit())
            (top_left, _, bottom_right, _) = bbox
            x_min, y_min = int(top_left[0]), int(top_left[1])
            x_max, y_max = int(bottom_right[0]), int(bottom_right[1])
            crop = gray[max(0, y_min-5):y_max+5, max(0, x_min-5):x_max+5]

            mem_pred, mem_conf = self.style_memory.predict_symbol(crop)
            final_val = mem_pred if mem_conf > 0.8 else clean_num

            if mem_conf > 0.8:
                high_confidence_matches += 1

            if final_val and final_val.isdigit():
                val = float(final_val)
                if 200 <= val <= 3000:
                    numbers.append(val)
                    if crop.size > 0:
                        crops_for_training.append({"val": val, "crop": crop})

        numbers.sort(reverse=True)

        if len(numbers) >= 2 and (prob > 0.6 or high_confidence_matches > 0):
            engine_used = "Local Memory Engine (Fast)"
            height = numbers[0]
            width = numbers[1]
        else:
            engine_used = "Vision LLM Fallback (Deep Parse)"
            vllm_dims = self.parse_with_vllm(image_bytes)
            width = vllm_dims["width_mm"]
            height = vllm_dims["height_mm"]

        cutouts = self.auto_place_hardware(width, height)
        panel = ParsedGlassPanel(panel_id=1, width_mm=width, height_mm=height, cutouts=cutouts)

        return panel, engine_used, crops_for_training