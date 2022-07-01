# practica-tecnologias-cloud-miax
[Dash application](https://practica-tecnologias-cloud-miax-texwf7ckua-no.a.run.app) showing the implied volatility of MINI IBEX options.

Every day a lambda function does web scraping from [this web](https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35) calculates the volatilities and stores the data in DynamoDB ([code](https://github.com/Tonarro/devops-lambda-data-meff)). 

The application allows to compare volatility skews on different days. It also allows to visualize the volatility surface and its evolution over time.
