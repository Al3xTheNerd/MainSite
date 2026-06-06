from flask import render_template, request, flash, redirect, url_for, jsonify
from core import app, db
from core.decorators.auth import permission_level_required
from flask_login import current_user
from typing import List, Dict, Any
import re
from core.models.items import Items
from core.models.shopLogs import ShopLogs
from core.models.user import User

import time
def sortDict(data: Dict[Any, int | float], reverse: bool = False) -> Dict[Any, int | float]:
    sorted_dict = dict(sorted(data.items(), key=lambda item: item[1], reverse = reverse))
    return sorted_dict

def hasAccessToShop(shopOwner) -> bool:
    shopInfo: User | None = User.query.filter(User.username==shopOwner).one_or_none()
    if isinstance(shopInfo, User):
        if current_user.adminPermissions == 100:
            return True
        if shopInfo.staffMembers:
            allowedUsers = shopInfo.staffMembers.split(",")
            print(allowedUsers)
            if "public" in allowedUsers:
                return True
            for user in allowedUsers:
                if current_user.username.lower() == user.lower():
                    return True
    return False

def ShopTime(days, username):
    itemList: List[Items] = Items.query.filter_by(ShopOwner=username, Excluded=0).all()
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
    
    transactionLogs: List[ShopLogs] = ShopLogs.query.filter(ShopLogs.ShopOwner == username, ShopLogs.TimeStamp >= EpochTimeFrame).all()
    CashSpentOnBuying = 0.0
    
    CashEarnedFromSelling = 0.0
    for log in transactionLogs:
        if log.Item not in newItemList.keys():
            continue
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
    return stats, newItemList

@permission_level_required(10)
@app.route('/shop/time/<days>')
def ShopTimeSelf(days):
    stats, newItemList = ShopTime(days, current_user.username)
    return render_template("shopStuff/index.html", stats = stats, ItemList = newItemList)

@permission_level_required(0)
@app.route('/shop/time/<days>/<username>')
def ShopTimeOthers(days, username):
    if hasAccessToShop(username):
        stats, newItemList = ShopTime(days, username)
        return render_template("shopStuff/index_others.html", stats = stats, ItemList = newItemList, shopOwner = username)
    flash("You do not have access to this shop. Try again if you feel this is an error.")
    return redirect(url_for("index"))

def ShopTransactions(username):
    transactionLogs: List[ShopLogs] = ShopLogs.query.filter_by(ShopOwner=username).all()
    itemList: List[Items] = Items.query.filter_by(ShopOwner=username).all()
    newItemList = {}
    for item in itemList:
        newItemList[item.id] = item
    for log in transactionLogs:
        match log.Type:
            case "to":
                log.Type = "Buy"
            case "from":
                log.Type = "Sell"
    transactionLogs.reverse()
    return transactionLogs, newItemList

@permission_level_required(10)
@app.route('/shop/transactions')
def ShopTransactionsSelf():
    transactionLogs, newItemList = ShopTransactions(current_user.username)
    return render_template("shopStuff/transactionList.html", TransactionLogs=transactionLogs, ItemList = newItemList)

@permission_level_required(0)
@app.route('/shop/transactions/<username>')
def ShopTransactionsOthers(username):
    if hasAccessToShop(username):
        transactionLogs, newItemList = ShopTransactions(username)
        return render_template("shopStuff/transactionList_others.html", TransactionLogs=transactionLogs, ItemList = newItemList, shopOwner = username)
    flash("You do not have access to this shop. Try again if you feel this is an error.")
    return redirect(url_for("index"))


@permission_level_required(10)
@app.route('/shop/items')
def ShopItems(): 
    itemList: List[Items] = Items.query.filter(Items.ShopOwner==current_user.username, Items.Excluded != 1 ).all()

    return render_template("shopStuff/itemList.html", ItemList = itemList)

@permission_level_required(10)
@app.route('/shop/excludedItems')
def ShopExcludedItems(): 
    itemList: List[Items] = Items.query.filter(Items.ShopOwner==current_user.username, Items.Excluded != 0 ).all()

    return render_template("shopStuff/excludedItemList.html", ItemList = itemList)

@permission_level_required(0)
@app.route('/shop/items/<username>')
def ShopItemsOthers(username): 
    if hasAccessToShop(username):
        itemList: List[Items] = Items.query.filter_by(ShopOwner=username).all()
        return render_template("shopStuff/itemList_others.html", ItemList = itemList, shopOwner = username)
    flash("You do not have access to this shop. Try again if you feel this is an error.")
    return redirect(url_for("index"))

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
@app.route('/shop/excludeItem/<itemID>', methods=['GET'])
def ShopExcludeItem(itemID): 
    item: Items | None= Items.query.filter(Items.id == itemID).one_or_none()
    if isinstance(item, Items):
        if item.ShopOwner == current_user.username:
            item.Excluded = 1;
            db.session.commit()
            flash(f"Excluded <code>{item.Name}</code> from the item list and general statistics.")
            return redirect(url_for("ShopItems"))
        else:
            flash("This item does not belong to your shops. Please try again.")
            return redirect(url_for("ShopItems"))
    else:
        flash("This item does not exist. Please try again.")
        return redirect(url_for("ShopItems"))

@permission_level_required(10)
@app.route('/shop/includeItem/<itemID>', methods=['GET'])
def ShopIncludeItem(itemID): 
    item: Items | None= Items.query.filter(Items.id == itemID).one_or_none()
    if isinstance(item, Items):
        if item.ShopOwner == current_user.username:
            item.Excluded = 0;
            db.session.commit()
            flash(f"Re-included <code>{item.Name}</code> into the item list and general statistics.")
            return redirect(url_for("ShopExcludedItems"))
        else:
            flash("This item does not belong to your shops. Please try again.")
            return redirect(url_for("ShopExcludedItems"))
    else:
        flash("This item does not exist. Please try again.")
        return redirect(url_for("ShopExcludedItems"))

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


@permission_level_required(10)
@app.route('/shop/manageStaff')
def ShopSetStaff(): 
    return render_template("shopStuff/setStaff.html")

@permission_level_required(10)
@app.route('/shop/manageStaff', methods= ["POST"])
def ShopSetStaff_POST():
    staffMembers = request.form.get("staffMembers")
    
    current_user.staffMembers = staffMembers
    
    db.session.commit()
    flash(f"Staff set to <code>{current_user.staffMembers}.</code>")

    return redirect(url_for("ShopTimeSelf", days=3))


@permission_level_required(0)
@app.route('/shop/otherShops')
def ShopViewShops(): 
    allShops: List[User] = User.query.filter(User.adminPermissions >= 10).all()
    shopsToShow = []
    for shop in allShops:
        if hasAccessToShop(shop.username):
            shopsToShow.append(shop)
    return render_template("shopStuff/others_list.html", ShopList = shopsToShow)

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
        item.Excluded = 0
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

@permission_level_required(100)
@app.route('/shop/fixOldLogs')
def ShopFixOld():
    transactionLogs: List[ShopLogs] = ShopLogs.query.filter_by(ShopOwner=current_user.username, Type="to", Money=0.0).all()
    itemList: List[Items] = Items.query.filter_by(ShopOwner=current_user.username).all()
    
    buyPrices: Dict[int, float] = {item.id: item.BuyPrice for item in itemList}
    totalChanged = 0.0
    transactionsChanged = 0
    for log in transactionLogs:
        old = log.Money
        log.Money = round(buyPrices[log.Item] * log.Quantity, 2)
        if old != log.Money:
            totalChanged += (log.Money - old)
            transactionsChanged += 1
    flash(f"{transactionsChanged} total transactions updated. -${round(totalChanged, 2)} accounted for.")
    db.session.commit()
    return redirect(url_for('ShopTimeSelf', days=3))


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
                pattern = r"(\w+)\s+purchased\s+(\d+)\s+(.+?)\s+from your shop, and you earned\s+\$([\d,]+(?:\.\d+)?)"
                match = re.search(pattern, message["message"])
                if match:
                    name = match.group(1)
                    quantity = int(match.group(2))
                    item = match.group(3)
                    dollars = float(match.group(4).replace(',', ''))
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

