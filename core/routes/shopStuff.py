from flask import render_template, request, flash, redirect, url_for, jsonify
from core import app, db
from core.decorators.auth import permission_level_required
from flask_login import current_user
from typing import List, Dict, Any
import re
from core.models.items import Items
from core.models.shopLogs import ShopLogs
from core.models.user import User
from core.models.shops import Shops

defaultShopName = "Default (Unsorted)"

import time
def sortDict(data: Dict[Any, int | float], reverse: bool = False) -> Dict[Any, int | float]:
    sorted_dict = dict(sorted(data.items(), key=lambda item: item[1], reverse = reverse))
    return sorted_dict

def hasAccessToShop(shopOwner, staffList) -> bool:
    if current_user.adminPermissions == 100:
        return True
    if current_user.username == shopOwner:
        return True
    if staffList:
        allowedUsers = staffList.split(",")
        if "public" in allowedUsers:
            return True
        for user in allowedUsers:
            if current_user.username.lower() == user.lower():
                return True
    return False

def ShopTime(days, username, shopID):
    itemList: List[Items] = Items.query.filter_by(ShopOwner=username, Excluded=0, Shop=shopID).all()
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
    ItemsBought = 0 
    ItemsSold = 0 
    for log in transactionLogs:
        if log.Item not in newItemList.keys():
            continue
        if log.Type == "to":
            if log.Money:
                CashSpentOnBuying += log.Money
            ItemsBought += log.Quantity
            PeopleWhoSoldTheMost[log.Interactor] = PeopleWhoSoldTheMost.get(log.Interactor, 0) + log.Quantity
            MostPurchasedItems[log.Item] = MostPurchasedItems.get(log.Item, 0) + log.Quantity
        else:
            if log.Money:
                CashEarnedFromSelling += log.Money
                PeopleWhoBoughtTheMostValue[log.Interactor] = PeopleWhoBoughtTheMostValue.get(log.Interactor, 0) + log.Money
            ItemsSold += log.Quantity
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
        "defaults" : defaultTimes,
        "SoldQuantity" : ItemsSold,
        "BoughtQuantity" : ItemsBought
    }
    return stats, newItemList


@permission_level_required(0)
@app.route('/shop/time/<username>/<shopID>/<days>')
def ShopTimeView(username: str, shopID: int, days:int):
    shopID = int(shopID)
    shopName = None
    if shopID == 0:
        shopName = defaultShopName
        user = User.query.filter(User.username == username).one_or_none()
        if not isinstance(user, User):
            flash("Shop does not exist.")
            return redirect(url_for("ShopViewShops"))
        else:
            if hasAccessToShop(user.username, user.staffMembers):
                stats, newItemList = ShopTime(days, user.username, 0)
            else:
                flash("Shop does not exist.")
                return redirect(url_for("ShopViewShops"))
    else:
        shop = Shops.query.filter(Shops.owner == username, Shops.id == shopID).one_or_none()
        if not isinstance(shop, Shops):
            flash("Shop does not exist.")
            return redirect(url_for("ShopViewShops"))
        else:
            if hasAccessToShop(shop.owner, shop.staffMembers):
                shopName = shop.name
                stats, newItemList = ShopTime(days, username, shopID)
            else:
                flash("Shop does not exist.")
                return redirect(url_for("ShopViewShops"))
    return render_template("shopStuff/index.html", stats = stats, ItemList = newItemList, shopName = shopName, shopID = shopID, username = username)


def ShopTransactions(username, shopID):
    transactionLogs: List[ShopLogs] = ShopLogs.query.filter_by(ShopOwner=username).all()
    itemList: List[Items] = Items.query.filter_by(ShopOwner=username, Shop=shopID).all()
    newItemList = {}
    for item in itemList:
        newItemList[item.id] = item
    newLogs = []
    for log in transactionLogs:
        if log.Item in newItemList:
            match log.Type:
                case "to":
                    log.Type = "Buy"
                case "from":
                    log.Type = "Sell"
            newLogs.append(log)
    newLogs.reverse()
    return newLogs, newItemList

@permission_level_required(0)
@app.route('/shop/transactions/<username>/<shopID>')
def ShopTransactionsView(username, shopID):
    shopID = int(shopID)
    if shopID == 0:
        shopName = defaultShopName
        user = User.query.filter(User.username == username).one_or_none()
        if not isinstance(user, User):
            flash("Shop does not exist.")
            return redirect(url_for("ShopViewShops"))
        else:
            staffList = user.staffMembers
    else:
        shop = Shops.query.filter(Shops.owner == username, Shops.id == shopID).one_or_none()
        if not isinstance(shop, Shops):
            flash("Shop does not exist.")
            return redirect(url_for("ShopViewShops"))
        else:
            shopName = shop.name
            staffList = shop.staffMembers
    if hasAccessToShop(username, staffList):
        transactionLogs, newItemList = ShopTransactions(username, shopID)
        return render_template("shopStuff/transactionList.html", TransactionLogs=transactionLogs, ItemList = newItemList, shopOwner = username, shopName= shopName)
    flash("Shop does not exist.")
    return redirect(url_for("index"))


@permission_level_required(10)
@app.route('/shop/items/<username>/<shopID>')
def ShopItems(username, shopID): 
    shopID = int(shopID)
    if shopID == 0:
        shopName = defaultShopName
        user = User.query.filter(User.username == username).one_or_none()
        if not isinstance(user, User):
            flash("Shop does not exist.")
            return redirect(url_for("ShopViewShops"))
        else:
            owner = user.username
            staffList = user.staffMembers
    else:
        shop = Shops.query.filter(Shops.owner == username, Shops.id == shopID).one_or_none()
        if not isinstance(shop, Shops):
            flash("Shop does not exist.")
            return redirect(url_for("ShopViewShops"))
        else:
            owner = shop.owner
            shopName = shop.name
            staffList = shop.staffMembers
    if hasAccessToShop(username, staffList):
        itemList: List[Items] = Items.query.filter(Items.ShopOwner==username, Items.Excluded != 1, Items.Shop == shopID).all()
        if owner == current_user.username:
            isOwn = True
        else:
            isOwn = False
        return render_template("shopStuff/itemList.html", ItemList = itemList, shopName = shopName, username = username, isOwn = isOwn)
    flash("Shop does not exist.")
    return redirect(url_for("ShopViewShops"))

@permission_level_required(10)
@app.route('/shop/excludedItems')
def ShopExcludedItems(): 
    itemList: List[Items] = Items.query.filter(Items.ShopOwner==current_user.username, Items.Excluded != 0 ).all()

    return render_template("shopStuff/excludedItemList.html", ItemList = itemList)


@permission_level_required(10)
@app.route('/shop/manageItem/<itemID>')
def ShopManageItem(itemID):
    currentShops = currentShopsData()
    item: Items | None= Items.query.filter(Items.id == itemID).one_or_none()
    if isinstance(item, Items):
        if item.ShopOwner == current_user.username:
            return render_template("shopStuff/manageItem.html", item = item, currentShops = currentShops)
        else:
            flash("This item does not belong to your shops. Please try again.")
            return redirect(url_for("ShopViewShops"))
    else:
        flash("This item does not exist. Please try again.")
        return redirect(url_for("ShopViewShops"))

@permission_level_required(10)
@app.route('/shop/manageItem/<itemID>', methods=["POST"])
def ShopManageItem_POST(itemID): 
    item: Items | None= Items.query.filter(Items.id == itemID).one_or_none()
    if isinstance(item, Items):
        if item.ShopOwner == current_user.username:
            buyPrice = request.form.get("buyPrice")
            sellPrice = request.form.get("sellPrice")
            stock = request.form.get("stock")
            shop = int(request.form.get("Shop", 0))
            
            item.Shop = shop
            item.BuyPrice = buyPrice
            item.SellPrice = sellPrice
            item.StockLevel = stock
            
            db.session.commit()
            flash(f"{item.Name} updated successfully.")
        else:
            flash("This item does not belong to your shops. Please try again.")
    else:
        flash("This item does not exist. Please try again.")
    return redirect(url_for("ShopViewShops"))

@permission_level_required(10)
@app.route('/shop/bulkChangeShops', methods=["GET"])
def ShopBulkChangeShops():
    validItems = Items.query.filter(Items.ShopOwner == current_user.username).all()
    shops = currentShopsData()
    return render_template("shopStuff/bulkShopChanges.html", validItems = validItems, currentShops = shops)

@permission_level_required(10)
@app.route('/shop/bulkChangeShopsUnsortedOnly', methods=["GET"])
def ShopBulkChangeShopsUnsortedOnly():
    validItems = Items.query.filter(Items.ShopOwner == current_user.username, Items.Shop == 0).all()
    shops = currentShopsData()
    return render_template("shopStuff/bulkShopChanges.html", validItems = validItems, currentShops = shops)

@permission_level_required(10)
@app.route('/shop/bulkChangeShopsUnsortedOnly', methods=["POST"])
def ShopBulkChangeShopsUnsortedOnly_POST():
    validItems: List[Items] = Items.query.filter(Items.ShopOwner == current_user.username).all()
    shopID = int(request.form.get('Shop', 0))
    shop = Shops.query.filter(Shops.owner == current_user.username, Shops.id == shopID).one_or_none()
    if not isinstance(shop, Shops) and shopID != 0:
        flash("Shop does not exist.")
        return redirect(url_for("ShopViewShops"))
    if shopID == 0:
        shopName = defaultShopName
    else:
        shopName = shop.name # type: ignore
    items = [int(x) for x in request.form.getlist("items")]
    changeCounter = 0
    for item in validItems:
        if item.id in items:
            if item.Shop != shopID:
                item.Shop = shopID
                changeCounter += 1
    db.session.commit()
    flash(f"<code>{changeCounter}</code> items swapped to be part of <code>{shopName}</code>")
    return redirect(url_for("ShopBulkChangeShops"))

@permission_level_required(10)
@app.route('/shop/bulkChangeShops', methods=["POST"])
def ShopBulkChangeShops_POST():
    validItems: List[Items] = Items.query.filter(Items.ShopOwner == current_user.username).all()
    shopID = int(request.form.get('Shop', 0))
    shop = Shops.query.filter(Shops.owner == current_user.username, Shops.id == shopID).one_or_none()
    if not isinstance(shop, Shops) and shopID != 0:
        flash("Shop does not exist.")
        return redirect(url_for("ShopViewShops"))
    if shopID == 0:
        shopName = defaultShopName
    else:
        shopName = shop.name # type: ignore
    items = [int(x) for x in request.form.getlist("items")]
    changeCounter = 0
    for item in validItems:
        if item.id in items:
            if item.Shop != shopID:
                item.Shop = shopID
                changeCounter += 1
    db.session.commit()
    flash(f"<code>{changeCounter}</code> items swapped to be part of <code>{shopName}</code>")
    return redirect(url_for("ShopBulkChangeShops"))


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
@app.route('/shop/excludeItem/<itemID>', methods=['GET'])
def ShopExcludeItem(itemID): 
    item: Items | None= Items.query.filter(Items.id == itemID).one_or_none()
    if isinstance(item, Items):
        if item.ShopOwner == current_user.username:
            item.Excluded = 1;
            db.session.commit()
            flash(f"Excluded <code>{item.Name}</code> from the item list and general statistics.")
            return redirect(url_for("ShopViewShops"))
        else:
            flash("This item does not belong to your shops. Please try again.")
            return redirect(url_for("ShopViewShops"))
    else:
        flash("This item does not exist. Please try again.")
        return redirect(url_for("ShopViewShops"))




def currentShopsData():
    user: User | None = User.query.filter(User.username == current_user.username).one_or_none()
    if not isinstance(user, User):
        return None
    shops: List[Shops] | None = Shops.query.filter(Shops.owner == current_user.username).all()
    formattedShops = {
        0 : {
            "ShopName" : defaultShopName,
            "StaffMembers" : user.staffMembers
        }
    }
    for shop in shops:
        formattedShops[shop.id] = {
            "ShopName" : shop.name,
            "StaffMembers" : shop.staffMembers
        }
    return formattedShops

def verifyShopName(name: str):
    problems = 0
    if len(name) == 0:
        flash("Shop Name must be at least 1 character long")
        problems += 1
    return False if problems else True

@permission_level_required(10)
@app.route('/shop/manageShops', methods=['GET'])
def ShopManageShops():
    currentShops = currentShopsData()
    return render_template("shopStuff/manageShops.html", currentShops = currentShops)

@permission_level_required(10)
@app.route('/shop/manageShops', methods=['POST'])
def ShopManageShopsPOST():
    forms = request.form.to_dict()
    if "New" in forms and verifyShopName(forms["ShopName"]): # New Shop
        newShop = Shops(name = forms["ShopName"], owner = current_user.username, staffMembers = forms["ShopStaff"]) #type:ignore
        db.session.add(newShop)
        db.session.commit()
        flash(f"<code>{forms['ShopName']}</code> added with the following staff: <code>{forms['ShopStaff']}</code>!")
    if "Edit" in forms: # Edit a shop
        if forms["Shop"] == '0': # Default unsorted shop
            user: User | None = User.query.filter(User.id == current_user.id).one_or_none()
            if isinstance(user, User):
                user.staffMembers = forms["ShopStaff"]
        else: # custom made shops
            shop: Shops | None = Shops.query.filter(Shops.id == forms["Shop"], Shops.owner == current_user.username).one_or_none()
            if not isinstance(shop, Shops):
                flash("Shop does not exist. Please try again.")
                return redirect(url_for("ShopManageShops"))
            if verifyShopName(forms["ShopName"]): # edit the name of an existing shop, will be blank if on default
                shop.name = forms["ShopName"]
                shop.staffMembers = forms["ShopStaff"]
        db.session.commit()
    if "Delete" in forms: # delete a shop
        shop: Shops | None = Shops.query.filter(Shops.id == forms["Shop"], Shops.owner == current_user.username).one_or_none()
        if isinstance(shop, Shops):
            items = Items.query.filter(Items.Shop == shop.id).all()
            for item in items:
                item.Shop = 0
            Shops.query.filter(Shops.id == forms["Shop"], Shops.owner == current_user.username).delete()
            db.session.commit()
            flash("Shop Deleted, and attached items moved to the unsorted category.")
        else:
            flash("Shop does not exist. Please try again.")
            return redirect(url_for("ShopManageShops"))
    return redirect(url_for("ShopManageShops"))

@permission_level_required(0)
@app.route('/shop/otherShops')
def ShopViewShops(): 
    allUsers: List[User] = User.query.filter(User.adminPermissions >= 10).all()
    allShops: List[Shops] = Shops.query.all()
    shopsToShow = []
    for user in allUsers:
        if hasAccessToShop(user.username, user.staffMembers):
            shopsToShow.append((user, False)) # false if it's an unsorted list
    for shop in allShops:
        if hasAccessToShop(shop.owner, shop.staffMembers):
            shopsToShow.append((shop, True)) # True if a proper shop
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
        item.Shop = 0 # 0 is default unsorted, can be organized later
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
        if "itemList" in message:
            print(message["itemList"])
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

