import nextcord
from nextcord.ext import commands
import requests
import json
from datetime import datetime

client = commands.Bot()
TOKEN = "insert your discord bot token"

@client.event
async def on_ready():
  print(f"{client.user.name} online")
  await client.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="status"))


@client.slash_command(name="code-check")
async def code_check(interaction, code):
    await interaction.response.send_message(".")
    await interaction.delete_original_message()

    headers = {"Authorization": f"Bearer {token['access_token']}"}
    data = requests.post(f"https://coderedemption-public-service-prod.ol.epicgames.com/coderedemption/api/shared/accounts/82b671e0d9b84f3cbe17dcd429ff102d/redeem/{code.replace('-', '')}/evaluate", headers=headers).json()

    if not "numericErrorCode" in data:
        product_data = requests.get(f"https://catalog-public-service-prod06.ol.epicgames.com/catalog/api/shared/bulk/offers?id={data['consumptionMetadata']['offerId']}", headers=headers).json()
        embed = nextcord.Embed(title=None, color=0x29a6d8)
        embed.add_field(name="Code", value=str(code).replace("-", "").upper()[:-5] + "XXXXX", inline=False)
        embed.add_field(name="Status", value=data["codeStatus"], inline=False)
        embed.add_field(name="Name", value=product_data[data["consumptionMetadata"]["offerId"]]["title"], inline=False)
        embed.add_field(name="Description", value=product_data[data["consumptionMetadata"]["offerId"]]["description"], inline=False)

        if "startDate" in data:
            embed.add_field(name="Starts", value=nextcord.utils.format_dt(datetime.strptime(data["startDate"], "%Y-%m-%dT%H:%M:%S.%fZ"), style="f"), inline=False)
        if "endDate" in data:
            embed.add_field(name="Expires", value=nextcord.utils.format_dt(datetime.strptime(data["endDate"], "%Y-%m-%dT%H:%M:%S.%fZ"), style="f"), inline=False)

        embed.add_field(name="Uses", value=f"**{data['completedCount']} ➤ {data['maxNumberOfUses']}**", inline=False)
        await interaction.followup.send(embed=embed)  # This is inside the async function, so it should work.
    else:
        # Handling error cases (numericErrorCode 19007, 19010, 19005)
        if data["numericErrorCode"] == 19007:
            embed = nextcord.Embed(title="Code not found", color=0xe3382c)
            await interaction.followup.send(embed=embed)
        elif data["numericErrorCode"] == 19010:
            embed = nextcord.Embed(title="Code used", color=0xe3382c)
            await interaction.followup.send(embed=embed)
        elif data["numericErrorCode"] == 19005:
            embed = nextcord.Embed(title="Code expired", color=0xe3382c)
            await interaction.followup.send(embed=embed)
    
    print(data)


@client.slash_command(name="login")
async def login(interaction):
    global embed
    embed = nextcord.Embed(title="loading", color=0x29a6d8)
    loading = await interaction.response.send_message(embed=embed, ephemeral=True)

    if str(interaction.user.id) in json.load(open("logins.json", "r")):
      database = json.load(open("logins.json", "r"))[str(interaction.user.id)]
      token = requests.post("https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token", headers={"Authorization":"basic OThmN2U0MmMyZTNhNGY4NmE3NGViNDNmYmI0MWVkMzk6MGEyNDQ5YTItMDAxYS00NTFlLWFmZWMtM2U4MTI5MDFjNGQ3"}, data={"grant_type":"device_auth", "account_id":database["account_id"], "device_id":database["device_id"], "secret":database["secret"]}).json()
      embed = nextcord.Embed(title=f"you are logged in as **{token['displayName']}**", color=0x29a6d8)
      await loading.edit(embed=embed)
    else:
      token = requests.post("https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token", headers={"Authorization":"basic OThmN2U0MmMyZTNhNGY4NmE3NGViNDNmYmI0MWVkMzk6MGEyNDQ5YTItMDAxYS00NTFlLWFmZWMtM2U4MTI5MDFjNGQ3"}, data={"grant_type":"client_credentials"}).json()
      req = requests.post("https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/deviceAuthorization", headers={"Authorization":f"bearer {token['access_token']}"}, data={"prompt":"login"}).json()
      embed = nextcord.Embed(title="Account login", description="1.Click the `Login` button below and login into your account.\n2.Confirm the prompt.\n3.Click the `Done` button below, the bot continues.", color=0x29a6d8)
      button_login = nextcord.ui.Button(label="Login", style=nextcord.ButtonStyle.link, url=req["verification_uri_complete"])
      button_done = nextcord.ui.Button(label="Done", style=nextcord.ButtonStyle.grey)
      async def button_done_callback(i):
        await i.response.defer()
        token = requests.post("https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token", headers={"Authorization":"basic OThmN2U0MmMyZTNhNGY4NmE3NGViNDNmYmI0MWVkMzk6MGEyNDQ5YTItMDAxYS00NTFlLWFmZWMtM2U4MTI5MDFjNGQ3"}, data={"grant_type":"device_code", "device_code":req["device_code"]}).json()
        if "errorMessage" in token:
          embed_error = nextcord.Embed(title="prompt not confirmed", color=0xe3382c)
          global embed
          await loading.edit(embeds=[embed, embed_error])
        else:
          device_auth = requests.post(f"https://account-public-service-prod.ol.epicgames.com/account/api/public/account/{token['account_id']}/deviceAuth", headers={"Authorization":f"Bearer {token['access_token']}"}).json()
          database = json.load(open("logins.json", "r"))
          database[str(i.user.id)] = {"device_id":device_auth["deviceId"], "account_id":device_auth["accountId"], "secret":device_auth["secret"]}
          json.dump(database, open("logins.json", "w"), indent=4)
          embed = nextcord.Embed(title=f"you are logged in as **{token['displayName']}**", color=0x29a6d8)
          await loading.edit(embeds=[embed], view=None)
      button_done.callback = button_done_callback
      view = nextcord.ui.View()
      view.add_item(button_login)
      view.add_item(button_done)
      await loading.edit(embed=embed, view=view)

client.run(TOKEN)
