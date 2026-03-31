import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app
from app.models.entities import ProductPriceSnapshot, ProductRaw, Retailer
from app.services.normalization import normalize_text

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    r1 = Retailer(name="Tesco", slug="tesco")
    r2 = Retailer(name="Asda", slug="asda")
    db.add_all([r1, r2])
    db.flush()
    p1 = ProductRaw(retailer_id=r1.id, provider_sku="T1", title="Heinz Baked Beans 415g", normalized_title=normalize_text("Heinz Baked Beans 415g"), brand="Heinz", category="tinned", size_value=415, size_unit="g", own_brand=False)
    p2 = ProductRaw(retailer_id=r2.id, provider_sku="A1", title="Asda Baked Beans 420g", normalized_title=normalize_text("Asda Baked Beans 420g"), brand="Asda", category="tinned", size_value=420, size_unit="g", own_brand=True)
    db.add_all([p1, p2])
    db.flush()
    db.add_all([
        ProductPriceSnapshot(product_raw_id=p1.id, price=1.4, unit_price=3.37),
        ProductPriceSnapshot(product_raw_id=p2.id, price=0.65, unit_price=1.55),
    ])
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    db.close()
