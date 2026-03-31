from abc import ABC, abstractmethod


class Provider(ABC):
    slug: str

    @abstractmethod
    def fetch_products(self) -> list[dict]: ...
