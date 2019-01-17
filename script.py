#Get exchange data for today and add it to list to plot rates historically
#Ver donde me hacen el mejor cambio hoy.
import csv
import datetime

import requests
from bs4 import BeautifulSoup


#Correct naming:
#    Dolar = USD
#    Peso Argentino = ARG
#    Real = Real
#    Unidad Indexada = UI
#    Libra Esterlina = GBP
#    Franco Suizo = Franco
#    Onza de Oro = ORO
#    Resto de las monedas: sin tilde
#    Indice Dow Jones=IDJ

allCurrencies = ["ARG", "Euro", "Real", "USD", "Franco", "Guarani", "IDJ",
                 "GBP", "ORO", "UI", "USD BROU", "Yen", "UR"]

def makeUruguayDecimalToUsDecimal(number):
    """Takes strings as 28.390,23 and turns them to 28390.23"""
    try:
        return number.replace(".", "").replace(",", ".")
    except AttributeError:
        print("Argument must be a string containing a number")


def getCambilexExchangeRate(url="http://www.cambilex.com.uy/"):
    """Gets exchange rates at Cambilex"""
    rCambilex = requests.get(url) #Abitab
    cambilexSoup = BeautifulSoup(rCambilex.text, "lxml")
    cotizacionesTable = cambilexSoup.find("div", {"class":"cotizaciones"}).find("table")

    data = {}
    for row in cotizacionesTable.find_all("tr")[1:]: #To skip headers
        #gets data for this currency
        moneda = row.find("td", {"class":"nombre"}).text.strip()

        if moneda == "Dolares Americanos":
            moneda = "USD"
        elif moneda == "Pesos Argentinos":
            moneda = "ARG"
        elif moneda == "Reales":
            moneda = "Real"
        elif moneda == "Euros":
            moneda = "Euro"

        compra = row.find("td", {"class":"compra"}).text.strip()
        venta = row.find("td", {"class":"venta"}).text.strip()
        #packs it up in dict
        data[moneda] = {"compra":float(compra), "venta":float(venta)}
    return data

def getIberiaExchangeRate(url="http://www.cambioiberia.com/?p=1"):
    """Gets exchange rates at Iberia"""
    rIberia = requests.get(url) #Cambio Iberia
    iberiaSoup = BeautifulSoup(rIberia.text, "lxml")
    cotizacionesTable = iberiaSoup.find("table")

    data = {}
    for row in cotizacionesTable.find_all("tr")[1:]: #To skip headers
        #gets data for this currency
        rowData = row.find_all("td")
        moneda = rowData[1].text
        if moneda == "Dólar":
            moneda = "USD"
        elif moneda == "Peso":
            moneda = "ARG"
        #Other currencies not necessary cause name is already correct.
        compra = rowData[2].text
        venta = rowData[3].text
        #packs it up in dict
        data[moneda] = {"compra":float(compra), "venta":float(venta)}
    return data

def getBrouExchangeRate(url="https://www.portal.brou.com.uy/cotizaciones"):
    """Gets exchange rates at Brou"""
    rBrou = requests.get(url)
    brouSoup = BeautifulSoup(rBrou.text, "lxml")
    cotizacionesTable = brouSoup.find("table")

    data = {}
    for row in cotizacionesTable.find_all("tr")[1:]: #To skip headers
        #gets data for this currency
        moneda = row.find("p", {"class":"moneda"}).text
        if moneda == "Dólar":
            moneda = "USD"
        elif moneda == "Dólar eBROU":
            moneda = "USD BROU"
        elif moneda == "Peso Argentino":
            moneda = "ARG"
        elif moneda == "Guaraní":
            moneda = "Guarani"
        elif moneda == "Libra Esterlina":
            moneda = "GBP"
        elif moneda == "Franco Suizo":
            moneda = "Franco"
        elif moneda == "Unidad Indexada":
            moneda = "UI"
        elif moneda == "Onza Troy De Oro":
            moneda = "ORO"
        elif moneda == "Indice Dow Jones":
            moneda = "IDJ"
        #Other currencies not necessary cause name is already correct.

        #Tira a la basura arbitrajes. Ends in 2 cause indexes are non inclusive
        #so [0:2] selects 0 and 1.
        compraVentaData = row.find_all("p", {"class":"valor"})[0:2]

        if moneda in ["UI", "IDJ"]:
            venta = makeUruguayDecimalToUsDecimal(compraVentaData[1].text.strip())
            data[moneda] = {"venta":float(venta)}
        else:
            compra = makeUruguayDecimalToUsDecimal(compraVentaData[0].text.strip())
            venta = makeUruguayDecimalToUsDecimal(compraVentaData[1].text.strip())
            data[moneda] = {"compra":float(compra), "venta":float(venta)}
    return data

def getBcuExchangeRate(url="http://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Cotizaciones.aspx"):
    """Gets exchange rates at BCU"""
    rBcu = requests.get(url)
    bcuSoup = BeautifulSoup(rBcu.text, "lxml")
    cotizacionesTable = bcuSoup.find("div", id="bcuCotizacionContent").find("div", {"class":"BCU_Form"}).find_all("table")[4]

    data = {}
    for row in cotizacionesTable.find_all("tr"): #To skip headers
        #gets data for this currency
        moneda = row.find("td", {"class":"Moneda "}) or row.find("td", {"class":"Moneda alt"})
        moneda = moneda.text #or because of different class names in the table

        if moneda == "DLS. USA BILLETE":
            moneda = "USD"
        elif moneda in ["DLS. USA CABLE", "DLS. USA FDO BCU", "DLS.PROMED.FONDO"]:
            moneda = "skip"
        elif moneda == "PESO ARG.BILLETE":
            moneda = "ARG"
        elif moneda == "REAL BILLETE":
            moneda = "Real"
        elif moneda == "UNIDAD INDEXADA":
            moneda = "UI"
        elif moneda == "UNIDAD REAJUSTAB":
            moneda = "UR"

        if moneda != "skip":
            venta = makeUruguayDecimalToUsDecimal(row.find("td", {"class":"Compra"}).text)
            data[moneda] = {"venta":float(venta)}
    return data

def addsMissingCurrenciesToDict(data, whatToAdd=-1):
    """Given data (dict), adds whatToAdd as {compra, venta} dict to every missing
    currency.
    """
    allCurrenciesInData = (key for key in data) #Generator to save memory
    missingCurrencies = (missing for missing in allCurrencies if missing not in allCurrenciesInData)
    valuesForMissing = {"compra":whatToAdd, "venta":whatToAdd}
    data.update({key:valuesForMissing for key in missingCurrencies})

def addMissingCurrencies(data, whatToAdd=-1):
    """Given data (dict or list), adds whatToAdd to every missing currency in
    every dict in the data list.
    """
    #Data can be a dict or a list of dicts
    if isinstance(data, dict):
        addsMissingCurrenciesToDict(data, whatToAdd)
    elif isinstance(data, list):
        for cambio in data:
            addsMissingCurrenciesToDict(cambio, whatToAdd)

def createTodayRow(startingRow, data):
    """Creates the row to write (i.e.: Adds currency data to the starting row)"""
    for key in sorted(data):
        try:
            startingRow = startingRow+[data[key]["compra"], data[key]["venta"]]
        except KeyError:
            startingRow = startingRow+[data[key]["venta"]]
    return startingRow

def writeCsvFileWithCondition(path, rowToWrite):
    """Writes rowToWrite to csv file in path if and only if the date has
    changed and at least one currency changed value.
    """
    with open(path, "a", newline="") as writeCsv, open(path, "r") as readCsv:
        #Gets last line of file by reading them all.
        reader = csv.reader(readCsv)
        for lastLine in reader:
            pass
        #I need to compare "date" field and all currencies.
        #If date doesn't change, don't write. If NO currency changes, don't write.
        lastDate = lastLine[0]
        #Grabs all currencies and turns them to floats for comparison.
        lastCurrencies = [float(x) for x in lastLine[3:]]

        if rowToWrite[0] != lastDate and rowToWrite[3:] != lastCurrencies:
            writer = csv.writer(writeCsv)
            writer.writerow(rowToWrite)

#####################################################

#Start of row with date data.
rightNow = datetime.datetime.today()
date = rightNow.strftime("%d-%m-%y")
time24 = rightNow.strftime("%H:%M:%S")
timeEpoch = rightNow.timestamp()
todayRow = [date, time24, timeEpoch]

#Grabs exchange rates from 4 different sources.
abitab = getCambilexExchangeRate()
abitabTodayRow = createTodayRow(todayRow, abitab)

redPagos = getIberiaExchangeRate()
redPagosTodayRow = createTodayRow(todayRow, redPagos)

brou = getBrouExchangeRate()
brouTodayRow = createTodayRow(todayRow, brou)

bcu = getBcuExchangeRate()
bcuTodayRow = createTodayRow(todayRow, bcu)

#Writes to the appropriate csv file if and only if we haven't run the program today
#and if at least one currency has changed.
writeCsvFileWithCondition("files/abitab.csv", abitabTodayRow)
writeCsvFileWithCondition("files/redPagos.csv", redPagosTodayRow)
writeCsvFileWithCondition("files/brou.csv", brouTodayRow)
writeCsvFileWithCondition("files/bcu.csv", bcuTodayRow)

#Gives which is the cheapest place to buy USD today.
if abitab["USD"]["venta"] < redPagos["USD"]["venta"]:
    print("El dolar es mas barato en Abitab")
else:
    print("El dolar es mas barato en RedPagos")

#TODO: Don't read all the file to get last line. Get the last line instead.
