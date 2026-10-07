from pydantic import BaseModel, Field

class ProductCard(BaseModel):
    product_id: str
    name: str
    price: float
    description: str
    colors: str = ""
    image_url: str

class StockBySize(BaseModel):
    size: str
    quantity: int

class ProductLookup(BaseModel):
    product_id: str
    name: str
    description: str
    colors: str
    price: float
    image_url: str
    sizes: list[StockBySize] = Field(default_factory=list)

class ChatReply(BaseModel):
    message: str = Field(description="A concise, friendly Campus Customs reply")
    products: list[ProductCard] = Field(default_factory=list, description="Relevant catalogue products")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
