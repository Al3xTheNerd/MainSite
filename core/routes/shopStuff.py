from flask import render_template, request, flash, redirect, url_for, jsonify
from core import app, db
from core.decorators.auth import permission_level_required
from flask_login import current_user
from typing import List, Dict, Any
from datetime import date, datetime, time as datetime_time, timedelta, timezone
import re
from core.models import (
    Items,
    ShopLogs,
    User,
    Shops,
    Outs
)

defaultShopName = "Default (Unsorted)"

import time
def sortDict(data: Dict[Any, int | float], reverse: bool = False) -> Dict[Any, int | float]:
    sorted_dict = dict(sorted(data.items(), key=lambda item: item[1], reverse = reverse))
    return sorted_dict

def hasAccessToShop(shopOwner, staffList) -> bool:
    if current_user.adminPermissions == 101:
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

def transaction_totals(logs: List[ShopLogs], item_ids: set[int]) -> dict:
    totals = {"sold": 0.0, "bought": 0.0, "sold_quantity": 0, "bought_quantity": 0, "transactions": 0}
    for log in logs:
        if log.Item not in item_ids or log.Type not in ("to", "from"):
            continue
        totals["transactions"] += 1
        if log.Type == "to":
            totals["bought"] += log.Money or 0
            totals["bought_quantity"] += log.Quantity or 0
        elif log.Type == "from":
            totals["sold"] += log.Money or 0
            totals["sold_quantity"] += log.Quantity or 0
    totals["sold"] = round(totals["sold"], 2)
    totals["bought"] = round(totals["bought"], 2)
    totals["net"] = round(totals["sold"] - totals["bought"], 2)
    return totals

def period_logs(username: str, start_ms: int, end_ms: int, filter_user: str | None = None) -> List[ShopLogs]:
    query = ShopLogs.query.filter(
        ShopLogs.ShopOwner == username,
        ShopLogs.TimeStamp >= start_ms,
        ShopLogs.TimeStamp < end_ms
    )
    if filter_user:
        query = query.filter(ShopLogs.Interactor == filter_user)
    return query.all()

def utc_datetime_from_ms(timestamp_ms: int) -> datetime:
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=timestamp_ms)

def ShopTime(days, username, shopID, filterUser: None | str = None,
             start_date: date | None = None, end_date: date | None = None):
    itemList: List[Items] = Items.query.filter_by(ShopOwner=username, Excluded=0, Shop=shopID).all()
    newItemList = {}
    for item in itemList:
        newItemList[item.id] = item
        
    defaultTimes = [3, 7, 14, 21, 28, 30, 60, 180, 365]
    if start_date is not None and end_date is not None:
        EpochTimeFrame = int(datetime.combine(start_date, datetime_time.min, timezone.utc).timestamp() * 1000)
        # The upper bound is exclusive, so every transaction on the end date is included.
        EndTimeFrame = int(datetime.combine(end_date, datetime_time.min, timezone.utc).timestamp() * 1000) + 24 * 60 * 60 * 1000
        period_label = f"{start_date.isoformat()} through {end_date.isoformat()} (UTC)"
    else:
        EndTimeFrame = int(time.time() * 1000)
        EpochTimeFrame = EndTimeFrame - (24 * int(days) * 60 * 60 * 1000)
        period_label = f"Last {days} Days"
    PreviousStart = EpochTimeFrame - (EndTimeFrame - EpochTimeFrame)
    
    PeopleWhoSoldTheMost = {}
    PeopleWhoSoldTheMostValue = {}
    PeopleWhoBoughtTheMost = {}
    PeopleWhoBoughtTheMostValue = {}
    
    MostPurchasedItems = {}
    MostSoldItems = {}
    
    transactionLogs = period_logs(username, EpochTimeFrame, EndTimeFrame, filterUser)
    previousLogs = period_logs(username, PreviousStart, EpochTimeFrame, filterUser)
    item_ids = set(newItemList)
    CashSpentOnBuying = 0.0 
    
    CashEarnedFromSelling = 0.0 
    ItemsBought = 0 
    ItemsSold = 0 
    InteractorList = set()
    item_performance = {}
    for log in transactionLogs:
        if log.Item not in item_ids or log.Type not in ("to", "from"):
            continue
        InteractorList.add(log.Interactor)
        item_row = item_performance.setdefault(log.Item, {
            "item_id": log.Item, "name": newItemList[log.Item].Name or f"Item #{log.Item}",
            "sold": 0.0, "bought": 0.0, "sold_quantity": 0,
            "bought_quantity": 0, "transactions": 0, "previous_sold": 0.0
        })
        item_row["transactions"] += 1
        if log.Type == "to":
            if log.Money:
                CashSpentOnBuying += log.Money
                PeopleWhoSoldTheMostValue[log.Interactor] = round(PeopleWhoSoldTheMostValue.get(log.Interactor, 0) + log.Money, 2)
                item_row["bought"] += log.Money
            ItemsBought += log.Quantity
            item_row["bought_quantity"] += log.Quantity
            PeopleWhoSoldTheMost[log.Interactor] = PeopleWhoSoldTheMost.get(log.Interactor, 0) + log.Quantity
            MostPurchasedItems[log.Item] = MostPurchasedItems.get(log.Item, 0) + log.Quantity
        elif log.Type == "from":
            if log.Money:
                CashEarnedFromSelling += log.Money
                PeopleWhoBoughtTheMostValue[log.Interactor] = round(PeopleWhoBoughtTheMostValue.get(log.Interactor, 0) + log.Money, 2)
                item_row["sold"] += log.Money
            ItemsSold += log.Quantity
            item_row["sold_quantity"] += log.Quantity
            PeopleWhoBoughtTheMost[log.Interactor] = PeopleWhoBoughtTheMost.get(log.Interactor, 0) + log.Quantity
            MostSoldItems[log.Item] = MostSoldItems.get(log.Item, 0) + log.Quantity
    NetAmount = round(CashEarnedFromSelling - CashSpentOnBuying, 2)
    previous_totals = transaction_totals(previousLogs, item_ids)
    current_totals = transaction_totals(transactionLogs, item_ids)
    for log in previousLogs:
        if log.Type == "from" and log.Item in item_performance:
            item_performance[log.Item]["previous_sold"] += log.Money or 0
    for row in item_performance.values():
        row["sold"] = round(row["sold"], 2)
        row["bought"] = round(row["bought"], 2)
        row["previous_sold"] = round(row["previous_sold"], 2)
        row["net"] = round(row["sold"] - row["bought"], 2)
        row["sales_change"] = round(row["sold"] - row["previous_sold"], 2)

    day_ms = 24 * 60 * 60 * 1000
    period_days = (EndTimeFrame - EpochTimeFrame + day_ms - 1) // day_ms
    bucket_days = 1 if period_days <= 31 else 7 if period_days <= 180 else 30
    bucket_ms = bucket_days * day_ms
    bucket_count = (EndTimeFrame - EpochTimeFrame + bucket_ms - 1) // bucket_ms
    trend = []
    for bucket_index in range(bucket_count):
        bucket_start = EpochTimeFrame + bucket_index * bucket_ms
        trend.append({
            "label": utc_datetime_from_ms(bucket_start).strftime(
                "%b %d, %Y" if start_date is not None else "%b %d, %Y %H:%M"
            ),
            "sold": 0.0, "bought": 0.0
        })
    for log in transactionLogs:
        if log.Item not in item_ids or log.Type not in ("to", "from"):
            continue
        bucket = trend[(log.TimeStamp - EpochTimeFrame) // bucket_ms]
        if log.Type == "to":
            bucket["bought"] += log.Money or 0
        elif log.Type == "from":
            bucket["sold"] += log.Money or 0
    trend_max = max([1.0] + [max(bucket["sold"], bucket["bought"]) for bucket in trend])
    for index, bucket in enumerate(trend):
        bucket["sold"] = round(bucket["sold"], 2)
        bucket["bought"] = round(bucket["bought"], 2)
        bucket["x"] = round(40 + (index + 0.5) * 720 / len(trend), 1)
        bucket["sold_y"] = round(190 - bucket["sold"] * 160 / trend_max, 1)
        bucket["bought_y"] = round(190 - bucket["bought"] * 160 / trend_max, 1)

    comparison = []
    for label, key in [
        ("Sales revenue", "sold"), ("Purchases", "bought"),
        ("Net cash flow", "net"), ("Items sold", "sold_quantity"),
        ("Items purchased", "bought_quantity"), ("Transactions", "transactions")
    ]:
        comparison.append({
            "label": label, "money": key in ("sold", "bought", "net"),
            "current": current_totals[key], "previous": previous_totals[key],
            "change": round(current_totals[key] - previous_totals[key], 2)
        })
    stats = {
        "bought" : round(CashSpentOnBuying, 2),
        "sold" : round(CashEarnedFromSelling, 2),
        "total" : NetAmount,
        "days" : days,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "period_label": period_label,
        "period_start_ms": EpochTimeFrame,
        "period_end_ms": EndTimeFrame,
        "previous_start_ms": PreviousStart,
        "previous_label": f"{utc_datetime_from_ms(PreviousStart):%Y-%m-%d %H:%M} to {utc_datetime_from_ms(EpochTimeFrame):%Y-%m-%d %H:%M} UTC",
        "transaction_count": current_totals["transactions"],
        "comparison": comparison,
        "item_performance": sorted(item_performance.values(), key=lambda row: (-row["sold"], -row["transactions"], row["name"])),
        "trend": trend,
        "trend_granularity": ("Daily" if start_date is not None else "24-hour") if bucket_days == 1 else "7-day" if bucket_days == 7 else "30-day",
        "trend_scale_max": round(trend_max, 2),
        "PeopleWhoSoldTheMost" : sortDict(PeopleWhoSoldTheMost, True),
        "PeopleWhoSoldTheMostValue" : sortDict(PeopleWhoSoldTheMostValue, True),
        "PeopleWhoBoughtTheMost" : sortDict(PeopleWhoBoughtTheMost, True),
        "PeopleWhoBoughtTheMostValue" : sortDict(PeopleWhoBoughtTheMostValue, True),
        "MostPurchasedItems" : sortDict(MostPurchasedItems, True),
        "MostSoldItems" : sortDict(MostSoldItems, True),
        "defaults" : defaultTimes,
        "SoldQuantity" : ItemsSold,
        "BoughtQuantity" : ItemsBought,
        "InteractorList": sorted(InteractorList)
    }
    return stats, newItemList, transactionLogs, previousLogs

def shop_performance(username: str, shop_names: dict[int, str],
                     current_logs: List[ShopLogs], previous_logs: List[ShopLogs]) -> list[dict]:
    rows = {
        shop_id: {
            "shop_id": shop_id, "name": name, "sold": 0.0, "bought": 0.0,
            "sold_quantity": 0, "bought_quantity": 0, "transactions": 0,
            "previous_sold": 0.0
        }
        for shop_id, name in shop_names.items()
    }
    if not rows:
        return []
    items = Items.query.filter(Items.ShopOwner == username, Items.Excluded == 0).all()
    item_shops = {item.id: item.Shop for item in items if item.Shop in rows}
    for log in current_logs:
        shop_id = item_shops.get(log.Item)
        if shop_id is None or log.Type not in ("to", "from"):
            continue
        row = rows[shop_id]
        row["transactions"] += 1
        if log.Type == "to":
            row["bought"] += log.Money or 0
            row["bought_quantity"] += log.Quantity or 0
        elif log.Type == "from":
            row["sold"] += log.Money or 0
            row["sold_quantity"] += log.Quantity or 0
    for log in previous_logs:
        shop_id = item_shops.get(log.Item)
        if shop_id is not None and log.Type == "from":
            rows[shop_id]["previous_sold"] += log.Money or 0
    for row in rows.values():
        row["sold"] = round(row["sold"], 2)
        row["bought"] = round(row["bought"], 2)
        row["previous_sold"] = round(row["previous_sold"], 2)
        row["net"] = round(row["sold"] - row["bought"], 2)
        row["sales_change"] = round(row["sold"] - row["previous_sold"], 2)
    return sorted(rows.values(), key=lambda row: (-row["sold"], row["name"]))


@permission_level_required(0)
@app.route('/shop/time/<username>/<shopID>/<days>', defaults = {'filterUser' : None})
@app.route('/shop/time/<username>/<shopID>/<days>/<filterUser>')

def ShopTimeView(username: str, shopID: int, days:int, filterUser: str | None):
    shopID = int(shopID)
    try:
        days = int(days)
        if not 1 <= days <= 3650:
            raise ValueError
    except ValueError:
        return "Invalid number of days.", 400
    start_date = end_date = None
    start_value = request.args.get("start_date")
    end_value = request.args.get("end_date")
    if start_value or end_value:
        try:
            if not start_value or not end_value:
                raise ValueError
            start_date = date.fromisoformat(start_value)
            end_date = date.fromisoformat(end_value)
            if (start_date.isoformat() != start_value or end_date.isoformat() != end_value
                    or start_date < date(1970, 1, 1) or start_date > end_date
                    or (end_date - start_date).days > 3650):
                raise ValueError
        except ValueError:
            flash("Enter start and end dates from 1970 onward, in order and no more than 10 years apart. Showing the selected number of days instead.")
            start_date = end_date = None
    shopName = None
    if shopID == 0:
        shopName = defaultShopName
        user = User.query.filter(User.username == username).one_or_none()
        if not isinstance(user, User):
            flash("Shop does not exist.")
            return redirect(url_for("ShopViewShops"))
        else:
            if hasAccessToShop(user.username, user.staffMembers):
                stats, newItemList, current_logs, previous_logs = ShopTime(days, user.username, 0, filterUser, start_date, end_date)
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
                stats, newItemList, current_logs, previous_logs = ShopTime(days, username, shopID, filterUser, start_date, end_date)
            else:
                flash("Shop does not exist.")
                return redirect(url_for("ShopViewShops"))
    owner = User.query.filter(User.username == username).one_or_none()
    visible_shops = {}
    if isinstance(owner, User) and hasAccessToShop(owner.username, owner.staffMembers):
        visible_shops[0] = defaultShopName
    for candidate in Shops.query.filter(Shops.owner == username).all():
        if hasAccessToShop(candidate.owner, candidate.staffMembers):
            visible_shops[candidate.id] = candidate.name
    stats["shop_performance"] = shop_performance(username, visible_shops, current_logs, previous_logs)
    utc_now = datetime.now(timezone.utc)
    return render_template(
        "shopStuff/index.html", stats=stats, ItemList=newItemList, shopName=shopName,
        shopID=shopID, username=username, filterUser=filterUser,
        current_utc_time=utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        current_utc_timestamp=int(utc_now.timestamp() * 1000),
        last_complete_utc_date=(utc_now.date() - timedelta(days=1)).isoformat(),
        range_is_incomplete=end_date is not None and end_date >= utc_now.date()
    )


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
                    log.Type = "Sold to Shop"
                case "from":
                    log.Type = "Purchased from Shop"
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

def ShopOuts(username, shopID, maxInStock):
    confirmedOuts: List[Outs] = Outs.query.filter_by(ShopOwner=username).all()
    itemList: List[Items] = Items.query.filter_by(ShopOwner=username, Shop=shopID).all()
    newItemList = {item.id: item for item in itemList}
    confirmedOutsForCurrentShop = [out for out in confirmedOuts if out.Item in newItemList]
    confirmedOutsForCurrentShop.reverse()
    estimatedOuts = [item for item in itemList if item.StockLevel <= int(maxInStock)]
    if len(estimatedOuts) == len(itemList):
        estimatedOuts = []
    return confirmedOutsForCurrentShop, estimatedOuts, newItemList

@permission_level_required(0)
@app.route('/shop/outs/<username>/<shopID>')
def ShopOutsView(username, shopID):
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
        ConfirmedOuts, EstimatedOuts, newItemList = ShopOuts(username, shopID, 0)
        if username == current_user.username:
            isOwn = True
        else:
            isOwn = False
        
        return render_template("shopStuff/outOfStocks.html", EstimatedOuts=EstimatedOuts, ConfirmedOuts=ConfirmedOuts, ItemList = newItemList, shopOwner = username, shopName= shopName, isOwn = isOwn, shopID = shopID)
    flash("Shop does not exist.")
    return redirect(url_for("ShopViewShops"))

def LowStock(username, shopID, maxInStock):
    itemList: List[Items] = Items.query.filter_by(ShopOwner=username, Shop=shopID).all()
    newItemList = {item.id: item for item in itemList}

    itemsUsingStockLevelMetrics = [item for item in itemList if item.MaxStock != 0 or item.LowStockAlert != 0]
    if len(itemsUsingStockLevelMetrics) >= 1:
        estimatedOuts = [item for item in itemList if item.StockLevel < item.LowStockAlert]
        usingMetrics = True
    else:
        estimatedOuts = [item for item in itemList if item.StockLevel <= int(maxInStock)]
        if len(estimatedOuts) == len(itemList):
            estimatedOuts = []
        usingMetrics = False
            
    return estimatedOuts, newItemList, usingMetrics

@permission_level_required(0)
@app.route('/shop/lowStock/<username>/<shopID>/<maxInStock>')
def ShopLowStockView(username, shopID, maxInStock):
    defaultLevels = [16, 32, 64, 128, 256, 512, 1024, 1728, 2048, 3456, 6912]
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
        EstimatedOuts, newItemList, usingMetrics = LowStock(username, shopID, maxInStock)
        if username == current_user.username:
            isOwn = True
        else:
            isOwn = False
        
        return render_template("shopStuff/lowStocks.html", EstimatedOuts=EstimatedOuts, ItemList = newItemList, shopOwner = username, shopName= shopName, isOwn = isOwn, shopID = shopID, defaultLevels = defaultLevels, usingMetrics= usingMetrics)
    flash("Shop does not exist.")
    return redirect(url_for("ShopViewShops"))

@permission_level_required(10)
@app.route('/shop/clearOut/<username>/<shopID>/<outID>', methods=['GET'])
def ShopClearOut(username, shopID, outID):
    out: Outs | None = Outs.query.filter(Outs.id == outID).one_or_none()
    if isinstance(out, Outs):
        if out.ShopOwner == current_user.username:
            db.session.commit()
            res = Outs.query.filter(Outs.id == outID).delete()
            if res > 0:
                db.session.commit()
                flash(f"Out alert cleared.")
            else:
                flash(f"Something went wrong.")
            return redirect(url_for("ShopOutsView", username = username, shopID = shopID))
        else:
            flash("This out does not belong to your shops. Please try again.")
            return redirect(url_for("ShopViewShops"))
    else:
        flash("This out does not exist. Please try again.")
        return redirect(url_for("ShopViewShops"))

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
            lowStock = request.form.get("lowStock")
            maxStock = request.form.get("maxStock")
            
            shop = int(request.form.get("Shop", 0))
            
            item.Shop = shop
            try:
                item.BuyPrice = float(buyPrice) # type:ignore
            except: pass
            try:
                item.SellPrice = float(sellPrice) # type:ignore
            except: pass
            if int(lowStock) <= int(maxStock): # type: ignore
                try:
                    item.LowStockAlert = int(lowStock) # type: ignore
                except: pass
                try:
                    item.MaxStock = int(maxStock) # type: ignore
                except: pass
            else:
                flash("Could not update Low Stock Alert/Maximum Stock. Low Stock Alert must be less than or equal to Maximum Stock")
            
            
            
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
@app.route('/shop/bulkChangeStockMetrics', methods=["GET"], defaults = {'shop' : None})
@app.route('/shop/bulkChangeStockMetrics/<shop>', methods=["GET"])
def ShopBulkChangeStockMetrics(shop: int | None):
    if shop:
        validItems = Items.query.filter(Items.ShopOwner == current_user.username, Items.Shop == shop).all()
    else:
        validItems = Items.query.filter(Items.ShopOwner == current_user.username).all()
    shops = currentShopsData()
    return render_template("shopStuff/bulkStockMetricChanges.html", validItems = validItems, currentShops = shops)

@permission_level_required(10)
@app.route('/shop/bulkChangeStockMetrics', methods=["POST"], defaults = {'shop' : None})
@app.route('/shop/bulkChangeStockMetrics/<shop>', methods=["POST"])
def ShopBulkChangeStockMetrics_POST(shop):
    validItems: List[Items] = Items.query.filter(Items.ShopOwner == current_user.username).all()
    lowStock = int(request.form.get('low', 0))
    maxStock = int(request.form.get('max', 0))
    if lowStock > maxStock:
        flash("<code>Low Stock Alert</code> must be less than or equal to the <code>Maximum Stock</code>")
        return redirect(url_for("ShopBulkChangeStockMetrics")) 
    items = [int(x) for x in request.form.getlist("items")]
    changeCounter = 0
    for item in validItems:
        if item.id in items:
            if item.LowStockAlert != lowStock:
                item.LowStockAlert = lowStock
                changeCounter += 1
            if item.MaxStock != maxStock:
                item.MaxStock = maxStock
                changeCounter += 1
    db.session.commit()
    flash(f"<code>{changeCounter}</code> items swapped to have <code>Low Stock Alert: {lowStock}</code>, <code>Maximum Stock: {maxStock}</code>")
    return redirect(url_for("ShopBulkChangeStockMetrics"))

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


def getOrCreateListing(ItemName: str, Action: str | None, Amount: int, PricePerItem: float | None = None, username = None) -> Items:
    if PricePerItem:
        UntaxedPrice = round(PricePerItem / 0.99, 2)
    item: Items | None = Items.query.filter_by(Name = ItemName, ShopOwner = username).first()
    if not item:
        item = Items()
        item.Name = ItemName
        item.StockLevel = 0
        currentStockLevel = 0
        item.BuyPrice = 0.00
        item.ShopOwner = username
        item.Excluded = 0
        item.Shop = 0 # 0 is default unsorted, can be organized later
        item.MaxStock = 0
        item.LowStockAlert = 0
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
        case None:
            pass
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
    for message in data["messages"]:
        appendStr = ""
        if "itemList" in message:
            appendStr += "("
            appendStr += ", ".join([f"{item}: {message['itemList'][item]}" for item in message["itemList"].keys()])
            appendStr += ")"
            if appendStr == "()":
                appendStr = ""
        print(message)
        match message["type"]:
            case "to":
                
                pattern = r"(\w+)\s+sold\s+(\d+)\s+(.+?)\s+to your shop for (?:\{3\}|\$([\d,]+(?:\.\d{1,2})?))\."
                #pattern = r"(\w+)\s+sold\s+(\d+)\s+(.+?)\s+to your shop\."
                match = re.search(pattern, message["message"])
                
                if match:
                    name = match.group(1)
                    quantity = int(match.group(2))
                    item = getOrCreateListing(match.group(3) + appendStr, "add", quantity, username=message["username"])
                    money = float(match.group(4).replace(',', ''))

                    item.BuyPrice = round(money/quantity, 2)
                    db.session.add(ShopLogs(Type = "to", Interactor = name, Quantity = quantity, Item = item.id, TimeStamp = message["time"], ShopOwner=message["username"], Money = money)) # type: ignore
            case "from":
                pattern = r"(\w+)\s+purchased\s+(\d+)\s+(.+?)\s+from your shop, and you earned\s+\$([\d,]+(?:\.\d+)?)"
                match = re.search(pattern, message["message"])
                if match:
                    name = match.group(1)
                    quantity = int(match.group(2))
                    dollars = float(match.group(4).replace(',', ''))
                    item = getOrCreateListing(match.group(3) + appendStr, "subtract", quantity, dollars/quantity, username=message["username"])
                    db.session.add(ShopLogs(Type = "from", Interactor = name, Quantity = quantity, Item = item.id, Money = dollars, TimeStamp = message["time"], ShopOwner=message["username"])) # type: ignore
            case "out":
                pattern = r"Your shop at (-?\d+),\s*(-?\d+),\s*(-?\d+) has run out of (.+)!"
                match = re.search(pattern, message["message"])
                if match:
                    x = int(match.group(1))
                    y = int(match.group(2))
                    z = int(match.group(3))
                    item = getOrCreateListing(match.group(4) + appendStr, None, 0, None, message["username"])
                    db.session.add(
                        Outs(Item = item.id, XCoord = x, YCoord = y, ZCoord = z, ShopOwner = message["username"])) # type: ignore
                    print(f"Shop at {x}, {y}, {z} ran out of {item}")
            case _:
                pass
        db.session.commit()
    return '', 200

