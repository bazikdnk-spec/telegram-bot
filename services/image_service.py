"""Task 20: Image service — fetch relevant photo from loremflickr by English prompt."""
import asyncio
import base64
import logging
import urllib.parse

import httpx

logger = logging.getLogger(__name__)

# Words → loremflickr tags that ACTUALLY return photos (tested)
KEYWORD_MAP = {
    "tomato": "tomato", "pizza": "pizza", "coffee": "coffee",
    "fruit": "fruit", "apple": "fruit", "bread": "bread", "cake": "cake",
    "food": "food", "burger": "food", "sushi": "food", "wine": "wine",
    "cat": "cat", "kitten": "cat", "dog": "dog", "puppy": "dog",
    "horse": "horse", "lion": "lion", "tiger": "tiger", "bird": "bird",
    "wolf": "wolf", "bear": "bear", "fox": "fox", "rabbit": "rabbit",
    "fish": "fish", "shark": "fish", "whale": "ocean",
    "mountain": "mountains", "mountains": "mountains", "hill": "mountains",
    "sunset": "sunset", "sunrise": "sunset", "dusk": "sunset",
    "ocean": "ocean", "sea": "ocean", "water": "ocean",
    "beach": "beach", "sand": "beach", "coast": "beach",
    "forest": "forest", "tree": "forest", "jungle": "forest", "wood": "forest",
    "flower": "flowers", "rose": "flowers", "tulip": "flowers",
    "snow": "snow", "ice": "snow", "winter": "snow", "frost": "snow",
    "sky": "sky", "cloud": "sky", "storm": "sky",
    "lake": "landscape", "river": "landscape", "waterfall": "waterfall",
    "desert": "desert", "canyon": "landscape",
    "city": "city", "town": "city", "urban": "city", "street": "street",
    "building": "architecture", "architecture": "architecture",
    "bridge": "bridge", "castle": "castle", "church": "architecture",
    "almaty": "city", "astana": "city", "kazakhstan": "mountains",
    "woman": "woman", "girl": "woman", "female": "woman", "lady": "woman",
    "man": "man", "boy": "man", "male": "man", "guy": "man",
    "baby": "baby", "child": "children", "children": "children", "kid": "children",
    "people": "people", "person": "people", "crowd": "people",
    "portrait": "portrait", "face": "portrait", "smile": "portrait",
    "car": "cars", "truck": "cars", "vehicle": "cars",
    "train": "train", "railroad": "train",
    "airplane": "airplane", "plane": "airplane", "aircraft": "airplane",
    "boat": "boat", "ship": "boat", "sailboat": "boat",
    "motorcycle": "motorcycle", "bike": "motorcycle",
    "art": "art", "painting": "art", "drawing": "art",
    "music": "music", "guitar": "guitar", "piano": "music",
    "sport": "sport", "football": "sport", "basketball": "sport",
    "technology": "technology", "computer": "technology", "robot": "technology",
    "space": "space", "galaxy": "space", "star": "space", "planet": "space",
    "fashion": "fashion", "dress": "fashion", "model": "fashion",
    "wedding": "wedding", "bride": "wedding",
    "vintage": "vintage", "retro": "vintage",
    "abstract": "abstract", "colorful": "abstract",
}


class ImageService:
    def __init__(self, settings, groq_service):
        self.settings = settings
        self.groq = groq_service
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0"},
        )

    async def close(self):
        await self._client.aclose()

    def _build_attempts(self, english_prompt: str) -> list[str]:
        """
        Build a list of tags to try on loremflickr — from most specific to fallback.
        1. Known mapped words (guaranteed to have photos)
        2. Actual words from the English prompt (Flickr has millions of tags)
        3. Final fallback: nature
        """
        attempts = []
        text_lower = english_prompt.lower()
        words = [
            w.strip(".,!?;:'\"")
            for w in text_lower.split()
            if len(w.strip(".,!?;:'\"")) > 2
        ]

        # Priority 1: check KEYWORD_MAP (guaranteed results)
        for word in words:
            if word in KEYWORD_MAP:
                tag = KEYWORD_MAP[word]
                if tag not in attempts:
                    attempts.append(tag)
                break

        # Priority 2: try actual words from the prompt directly in loremflickr
        # (Flickr has tags for: astronaut, volcano, pagoda, kimono, etc.)
        skip = {"the", "and", "with", "for", "very", "big", "small", "beautiful",
                "highly", "detailed", "photorealistic", "cinematic", "masterpiece",
                "quality", "resolution", "lighting", "dramatic", "vibrant"}
        for word in words[:5]:
            if word not in skip and word not in attempts:
                attempts.append(word)

        # Priority 3: absolute fallback
        if "nature" not in attempts:
            attempts.append("nature")

        return attempts

    async def generate_photo(self, english_prompt: str) -> bytes | None:
        """
        Fetch a relevant photo from loremflickr.
        Tries multiple tags derived from the English prompt — works for ANY subject.
        """
        attempts = self._build_attempts(english_prompt)
        seed = abs(hash(english_prompt)) % 99999
        logger.info(f"loremflickr attempts: {attempts[:4]} for '{english_prompt[:50]}'")

        for tag in attempts:
            encoded = urllib.parse.quote(tag)
            url = f"https://loremflickr.com/1024/768/{encoded}?lock={seed}"
            try:
                r = await self._client.get(url)
                ct = r.headers.get("content-type", "")
                final_url = str(r.url)

                if "defaultImage" in final_url:
                    logger.warning(f"defaultImage для '{tag}', пробую следующий")
                    seed = (seed + 3333) % 99999
                    continue

                if r.status_code == 200 and "image" in ct:
                    logger.info(f"OK tag='{tag}': {len(r.content)} байт")
                    return r.content

            except Exception as e:
                logger.error(f"loremflickr ошибка tag='{tag}': {e}")
            await asyncio.sleep(0.3)

        return None

    async def analyze_image(self, image_url: str, question: str = "Опиши это изображение подробно.") -> str:
        messages = [{"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]}]
        resp = await self.groq.client.chat.completions.create(
            messages=messages, model=self.groq.settings.vision_model,
        )
        return resp.choices[0].message.content

    async def analyze_image_bytes(self, image_bytes: bytes, mime_type: str = "image/jpeg", question: str = "Опиши изображение.") -> str:
        b64 = base64.b64encode(image_bytes).decode()
        return await self.analyze_image(f"data:{mime_type};base64,{b64}", question)
