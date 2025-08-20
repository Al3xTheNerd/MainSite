BackgroundImages = [
    ('light_gray_glazed_terracotta.webp', 'gray_glazed_terracotta.webp'),
]



Changelog = {
    "2/19/2025" : [
        ("mc-gold", "Added missing Olympus Quests."),
        ("mc-gold", "Corrected spelling mistake on Stats page."),
        ("mc-gold", "Setup auto deployment from dev environment.")
    ],
    "2/21/2025" : [
        ("mc-gold", "Added Item Tracker! Thank you SaltyAssassin for the suggestion!"),
        ("mc-gold", "Added Missing item (Mystic Boots)")
    ],
    "2/22/2025" : [
        ("mc-gold", "Moved the page showing all items to a secondary page, in an effort to help people with less than stellar internet connections still use the site. Thank you KaylaKrow for the suggestion!"),
        ("mc-gold", "Moved changelog to the main page.")
    ],
    "3/2/2025" : [
        ("mc-gold", "Reworked Navbar to bring me more joy."),
        ("mc-gold", "Added Infinite specific item tracker."),
        ("mc-gold", "Reworked database and created a database builder to make it easier to modify items."),
        ("mc-gold", "Added Elysium Pickaxe."),
        
    ],
    "3/8/2025" : [
        ("mc-gold", "Cosmic/Arcane Picks Win Chance 0.1%->0.06%")
    ],
    "3/9/2025" : [
        ("mc-gold", "Item/Infinite trackers now persistently store your items! Thank you Katie for the suggestion!")
    ],
    "3/16/2025" : [
        ("mc-gold", "Corrected a database error leading to no swords being listed under <a href=\"/tag/Weapons/Sword\">Swords</a>, thank you LostWoodsOne for bringing this to my attention!")
    ],
    "3/30/2025" : [
        ("mc-gold", "Added a <a href=\"/jobspayouts\">Jobs Payout Calculator</a>!"),
        ("mc-gold", "Added the new Trickster Crate!"),
        ("mc-gold", "Updated the Eternal Icesight to the new version!")
    ],
    "5/11/2025" : [
        ("mc-gold", "Added the newBloomfall Crate!")
    ],
    "6/3/2025" : [
        ("mc-gold", "Added <a href=\"/gamble\">Gambling</a>! Thank you BR_MarkoTheGamer for the suggestion!"),
        ("mc-gold", "Removed some redundant HTML tags (why were there 47 extra &lt;/li&gt; tags in the navbar??)"),
        ("mc-gold", "Added a Page View Tracker (again)")
    ],
    "6/5/2025" : [
        ("mc-green", "<a href=\"/gamble\">Gambling</a> is now weighted as it is in-game!"),
        ("mc-light-purple", "Cleaned up the Gambling Menu."),
        ("mc-green", "Added overviews to the gambling menu, so you can see what you got at a glance instead of looking through individually."),
        ("mc-light-purple", "Added a limit to how many rolls you could do at once. (turns out things get a bit wild when you try and roll 1,000,000 items :p)"),
        ("mc-red", "Corrected a bug where the changelog would break if you didn't also search for an item."),
        ("mc-red", "Pickaxes that appear in multiple crates now appear on their crate pages, they can also be pulled during gambling.")
    ],
    "6/11/2025" : [
        ("mc-blue", "Added the new Season 8: Astral crate!"),
        ("mc-red", "Corrected Bunny Helmet not showing up under <a href=\"/tag/Armor/Helmet\">Helmets</a>."),
        ("mc-gold", "Adjusted CSS (stupid fucking bootstrap) to be a bit more consistent and readable across the site."),
        ("mc-green", f"Made it so crate summaries for <a href=\"/gamble\">Gambling</a> show the colored item names."),
        ("mc-green", "Removed the silly gap space between tiles. (I'm still unsure if I like this better or not, may be reverted :s)")
    ],
    "6/14/2025" : [
        ("mc-gold", "Cleaned up some more HTML code."),
        ("mc-gold", "Standardized the code for displaying items into one file, to be shared across the site.")
    ],
    "7/7/2025" : [
        ("mc-green", "New tagging system, all items can now have up to 2 'keywords' (Offhand, Helmet) for better organization. This should help to narrow down searches a bit more."),
        ("mc-green", "Added item type to all items(minecraft:bow), should improve readability of site."),
        ("mc-green", "Slightly more automated changelog."),
        ("mc-green", "More navbar shenanigans!"),
        ("mc-light-purple", "Updated Jobs Payouts values as per <a href='https://discord.com/channels/1044076495095738408/1044080696915918848/1390464294331748482'>this update.</a>."),
        ("mc-gold", "Fully rewrote backend to support adding new items directly to the site. I was fully rebuilding the database previously with the old system."),
    ],
    "7/12/2025" : [
        ("mc-green", "Items can now support Tertiary Tags"),
        ("mc-gold", "RYUJIN (Season 6: Shogun) now tagged as Pickaxe, Axe, and Shovel"),
        ("mc-light-purple", "Gambling item limit 10,000 -> 1,000.")
    ],
    "7/19/2025" : [
        ("mc-red", "Corrected Quest Items showing in the same tag as the Quest papers themselves."),
        ("mc-green", "Added randomized background colors!"),
        ("mc-light-purple", "Navbar swapped over to dark mode."),
        ("mc-green", "Changelogs now use different colors to denote different types of updates, 5 free keys to the first person who correctly guesses my intent for each currently used color. (6/14 and earlier are not updated colors wise.)"),
        ("mc-light-purple", "Buffed out some corners around the site, tables are hopefully a little less jarring to look at.")
    ],
    "7/26/2025" : [
        ("mc-green", "Adjusted page titles to prettier names for each public page."),
        ("mc-green", "Adjusted website description to hopefully start showing up on google search when you type in MysticMC")
    ],
    "8/3/2025" : [
        ("mc-gold", "Whole new addition on the backend. I can now adjust the order that items appear in if I need to make adjustments later on. eg: I added Prometheus Level 2 and was able to put it nice and snug next to the Level 1. Before this update I would have had to manually remove every item from the database, and readd them to make a change like that."),
        ("mc-red", "Disabled the Masonry tiling, decided I don't love it."),
        ("mc-gold", "Backend Dashboard is now setup to supply the Discord Bot with a different item name as needed (prom level 2 and whatnot)"),
        ("mc-blue", "Eldritch Axe added."),
        ("mc-blue", "Mythril Greatsword added."),
        ("mc-blue", "Poseidon's Fury added."),
        ("mc-blue", "Aether Pickaxe added."),
        ("mc-blue", "Murakumo added."),
        ("mc-blue", "Olympus Orb (Level 3) added."),
        ("mc-blue", "Prometheus (Level 2) added."),
        ("mc-blue", "Hama Yumi added."),
        ("mc-blue", "Kitsune Shovel added."),
        ("mc-blue", "Mitsutama added."),
        ("mc-green", "Clicking an item on the bot or on the website will now take you to a screen showing far more detailed item information. Including tags or other notes that I've added (currently only 2 items have notes, see if you can find them)")
    ],
    "8/6/2025" : [
        ("mc-green", "Both Infinite tracker and Item tracker now generate a Discord formatted list, to make your shopping lists that much easier!")
    ],
    "8/18/2025" : [
        ("mc-green", "<a href=\"/search\">Advanced Search</a> is now available!")
    ]
}

        
Changelog = dict(reversed(list(Changelog.items())))