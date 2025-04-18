from flask import Flask, render_template, request, jsonify
import aiohttp
import asyncio
from flask_bootstrap import Bootstrap5
from config.config import settings
from services.spark_api import SparkAPIService
from models.schemas import DetailedCompanyData, StructureInfo

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')
bootstrap = Bootstrap5(app)
spark_service = SparkAPIService()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/search", methods=["POST"])
async def search():
    category = request.form.get("category")
    location = request.form.get("location")
    
    if not category or not location:
        return jsonify({"error": "Category and location are required"}), 400
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}/search",
                json={"category": category, "location": location}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return render_template("results.html", companies=result["companies"])
                else:
                    error_msg = await response.text()
                    return jsonify({"error": error_msg}), response.status
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/company/<inn>")
async def get_company_details(inn: str):
    """Получение подробной информации о компании"""
    try:
        # Получаем данные о компании из SPARK API
        company_details = await spark_service.get_company_info(inn)
        
        # Если данные не получены, создаем базовый объект с ИНН
        if not company_details:
            company_details = DetailedCompanyData(
                inn=inn,
                legal_name="Информация о компании",
                structure_info=StructureInfo()
            )
        
        # Добавляем логирование для отладки
        print(f"Company details for INN {inn}:")
        print(f"Legal name: {company_details.legal_name}")
        print(f"Full name: {company_details.full_name}")
        print(f"Status: {company_details.company_status}")
        print(f"Address: {company_details.address}")
        
        return render_template("company_details.html", company=company_details)
    except Exception as e:
        print(f"Error getting company details: {str(e)}")
        return render_template("company_details.html", 
                             company=DetailedCompanyData(
                                 inn=inn,
                                 legal_name="Ошибка получения данных",
                                 structure_info=StructureInfo()
                             ))

if __name__ == "__main__":
    app.run(
        host=settings.FLASK_HOST,
        port=settings.FLASK_PORT,
        debug=True
    ) 