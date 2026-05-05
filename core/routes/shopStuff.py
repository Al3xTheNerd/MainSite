from flask import render_template, request, flash, redirect, url_for, jsonify
from core import app, db
from core.decorators.auth import permission_level_required
from flask_login import current_user
from typing import List, Dict, Any
import re
from core.models.items import Items
from core.models.shopLogs import ShopLogs


import time
def sortDict(data: Dict[Any, int | float], reverse: bool = False) -> Dict[Any, int | float]:
    sorted_dict = dict(sorted(data.items(), key=lambda item: item[1], reverse = reverse))
    return sorted_dict

@permission_level_required(10)
@app.route('/shop/time/<days>')
def ShopTime(days):
    itemList: List[Items] = Items.query.filter_by(ShopOwner=current_user.username).all()
    newItemList = {}
    for item in itemList:
        newItemList[item.id] = item
        
    defaultTimes = [3, 7, 14, 21, 28, 30]
    EpochTimeFrame = int(time.time()*1000) - (24*int(days)*60*60*1000)
    
    PeopleWhoSoldTheMost = {}
    PeopleWhoBoughtTheMost = {}
    PeopleWhoBoughtTheMostValue = {}
    
    MostPurchasedItems = {}
    MostSoldItems = {}
    
    transactionLogs: List[ShopLogs] = ShopLogs.query.filter(ShopLogs.ShopOwner == current_user.username, ShopLogs.TimeStamp >= EpochTimeFrame).all()
    CashSpentOnBuying = 0.0
    
    
    CashEarnedFromSelling = 0.0
    for log in transactionLogs:
        if log.Type == "to":
            if log.Money:
                CashSpentOnBuying += log.Money
            PeopleWhoSoldTheMost[log.Interactor] = PeopleWhoSoldTheMost.get(log.Interactor, 0) + log.Quantity
            MostPurchasedItems[log.Item] = MostPurchasedItems.get(log.Item, 0) + log.Quantity
        else:
            if log.Money:
                CashEarnedFromSelling += log.Money
                PeopleWhoBoughtTheMostValue[log.Interactor] = PeopleWhoBoughtTheMostValue.get(log.Interactor, 0) + log.Money
            PeopleWhoBoughtTheMost[log.Interactor] = PeopleWhoBoughtTheMost.get(log.Interactor, 0) + log.Quantity
            MostSoldItems[log.Item] = MostSoldItems.get(log.Item, 0) + log.Quantity
    NetAmount = round(CashEarnedFromSelling - CashSpentOnBuying, 2)
    stats = {
        "bought" : round(CashSpentOnBuying, 2),
        "sold" : round(CashEarnedFromSelling, 2),
        "total" : NetAmount,
        "days" : days,
        "PeopleWhoSoldTheMost" : sortDict(PeopleWhoSoldTheMost, True),
        "PeopleWhoBoughtTheMost" : sortDict(PeopleWhoBoughtTheMost, True),
        "PeopleWhoBoughtTheMostValue" : sortDict(PeopleWhoBoughtTheMostValue, True),
        
        "MostPurchasedItems" : sortDict(MostPurchasedItems, True),
        "MostSoldItems" : sortDict(MostSoldItems, True),
        "defaults" : defaultTimes
    }
    return render_template("shopStuff/index.html", stats = stats, ItemList = newItemList)


@permission_level_required(10)
@app.route('/shop/transactions')
def ShopTransactions(): 
    transactionLogs: List[ShopLogs] = ShopLogs.query.filter_by(ShopOwner=current_user.username).all()
    itemList: List[Items] = Items.query.filter_by(ShopOwner=current_user.username).all()
    newItemList = {}
    for item in itemList:
        newItemList[item.id] = item
    for log in transactionLogs:
        match log.Type:
            case "to":
                log.Type = "Buy"
            case "from":
                log.Type = "Sell"
    return render_template("shopStuff/transactionList.html", TransactionLogs=transactionLogs, ItemList = newItemList)


@permission_level_required(10)
@app.route('/shop/items')
def ShopItems(): 
    itemList: List[Items] = Items.query.filter_by(ShopOwner=current_user.username).all()

    return render_template("shopStuff/itemList.html", ItemList = itemList)

@permission_level_required(10)
@app.route('/shop/manageItem/<itemID>')
def ShopManageItem(itemID): 
    item: Items | None= Items.query.filter(Items.id == itemID).one_or_none()
    if isinstance(item, Items):
        if item.ShopOwner == current_user.username:
            return render_template("shopStuff/manageItem.html", item = item)
        else:
            flash("This item does not belong to your shops. Please try again.")
            return redirect(url_for("ShopItems"))
    else:
        flash("This item does not exist. Please try again.")
        return redirect(url_for("ShopItems"))
    


@permission_level_required(10)
@app.route('/shop/manageItem/<itemID>', methods= ["POST"])
def ShopManageItem_POST(itemID): 
    item: Items | None= Items.query.filter(Items.id == itemID).one_or_none()
    if isinstance(item, Items):
        if item.ShopOwner == current_user.username:
            buyPrice = request.form.get("buyPrice")
            sellPrice = request.form.get("sellPrice")
            stock = request.form.get("stock")
            
            item.BuyPrice = buyPrice
            item.SellPrice = sellPrice
            item.StockLevel = stock
            
            db.session.commit()
            flash(f"{item.Name} updated successfully.")
        else:
            flash("This item does not belong to your shops. Please try again.")
    else:
        flash("This item does not exist. Please try again.")
    return redirect(url_for("ShopItems"))


def getOrCreateListing(ItemName: str, Action: str, Amount: int, PricePerItem: float | None = None, username = None) -> Items:
    if PricePerItem:
        UntaxedPrice = round(PricePerItem / 0.99, 2)
    item: Items | None = Items.query.filter_by(Name = ItemName, ShopOwner = username).one_or_none()
    if not item:
        item = Items()
        item.Name = ItemName
        item.StockLevel = 0
        currentStockLevel = 0
        item.BuyPrice = 0.00
        item.ShopOwner = username
        if PricePerItem:
            item.SellPrice = UntaxedPrice # type: ignore
        db.session.add(item)
        db.session.commit()
    currentStockLevel = item.StockLevel
    match Action:
        case "add":
            item.StockLevel = currentStockLevel + Amount
        case "subtract":
            item.StockLevel = currentStockLevel - Amount
            if item.StockLevel < 0:
                item.StockLevel = 0
        case "set":
            item.StockLevel = Amount
    if PricePerItem:
        item.SellPrice = UntaxedPrice # type: ignore
    db.session.commit()
    return item


@app.route('/shopconfig')
def ShopConfig():
    return jsonify(batch_seconds=15)

@app.route('/hook', methods=['POST'])
def hook():
    data = request.get_json()
    entries = []
    for message in data["messages"]:
        print(message)
        match message["type"]:
            case "to":
                pattern = r"(\w+)\s+sold\s+(\d+)\s+(.+?)\s+to your shop\."
                match = re.search(pattern, message["message"])
                if match:
                    name = match.group(1)
                    quantity = int(match.group(2))
                    item = match.group(3)
                    item = getOrCreateListing(match.group(3), "add", quantity, username=message["username"])
                    if item.BuyPrice != 0.00:
                        money = item.BuyPrice * quantity
                    else:
                        money = 0.0
                    db.session.add(ShopLogs(Type = "to", Interactor = name, Quantity = quantity, Item = item.id, TimeStamp = message["time"], ShopOwner=message["username"], Money = money)) # type: ignore
            case "from":
                pattern = r"(\w+)\s+purchased\s+(\d+)\s+(.+?)\s+from your shop, and you earned\s+\$(\d+(?:\.\d+)?)"
                match = re.search(pattern, message["message"])
                if match:
                    name = match.group(1)
                    quantity = int(match.group(2))
                    item = match.group(3)
                    dollars = float(match.group(4))
                    item = getOrCreateListing(match.group(3), "subtract", quantity, dollars/quantity, username=message["username"])
                    db.session.add(ShopLogs(Type = "from", Interactor = name, Quantity = quantity, Item = item.id, Money = dollars, TimeStamp = message["time"], ShopOwner=message["username"])) # type: ignore
            
            #case "out":
            #    pattern = r"run out of\s+(.+?)(?:!|$)"
            #    match = re.search(pattern, message["message"])
            #    if match:
            #        item = match.group(1)
            #        item = getOrCreateListing(match.group(1), "set", 0, username=message["username"])
            case _:
                pass
        db.session.commit()
            
    return '', 200

