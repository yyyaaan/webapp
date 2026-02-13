from pathlib import Path
from fastapi import APIRouter
import importlib.util
import logging

FEATURES_DIR = Path(__file__).parent.parent / "features"
logger = logging.getLogger(__name__)


class Feature:
    def __init__(self, name: str, router: APIRouter, url: str, description: str = ""):
        self.name = name
        self.router = router
        self.url = url
        self.description = description


def discover_features() -> list[Feature]:
    features: list[Feature] = []

    if not FEATURES_DIR.exists():
        return features

    for feature_dir in FEATURES_DIR.iterdir():
        if feature_dir.is_dir() and not feature_dir.name.startswith("_"):
            router_path = feature_dir / "router.py"
            if router_path.exists():
                try:
                    module_name = f"app.features.{feature_dir.name}.router"
                    spec = importlib.util.spec_from_file_location(module_name, router_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        if hasattr(module, "router") and hasattr(module, "feature_info"):
                            features.append(
                                Feature(
                                    name=module.feature_info.get("name", feature_dir.name),
                                    router=module.router,
                                    url=module.feature_info.get("url", f"/{feature_dir.name}"),
                                    description=module.feature_info.get("description", ""),
                                )
                            )
                except Exception as e:
                    logger.error(f"Failed to load feature {feature_dir.name}: {e}", exc_info=True)

    return features
