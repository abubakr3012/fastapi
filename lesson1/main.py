from fastapi import FastAPI,HTTPException
from pydantic import BaseModel

app=FastAPI()

class ProductCreate(BaseModel):
    name:str
    price:float

products=[]
next_id=1

@app.get('/products')
def get_products():
    return products

@app.get('/product/{product_id}')
def get_product(product_id:int):
    for i in products:
        if i['id']==product_id:
            return i

    raise HTTPException(status_code=404,detail='Product not found')

@app.post('/products')
def create_product(product:ProductCreate):
    global next_id

    new_product={
        'id':next_id,
        'name':product.name,
        'price':product.price
    }
    products.append(new_product)
    next_id+=1
    return new_product

@app.put('/product/{product_id}')
def update_product(product_id:int,product:ProductCreate):
    for i in products:
        if i['id']==product_id:
            i['name']=product.name
            i['price']=product.price
            return i

    raise HTTPException(status_code=404,detail='Product not found')

@app.delete('/product/{product_id}')
def delete_product(product_id:int):
    for i in products:
        if i['id']==product_id:
            products.remove(i)
            return {"message": "Product deleted successfully"}

    raise HTTPException(status_code=404,detail='Product not found')