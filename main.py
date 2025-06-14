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
    

client.run(TOKEN)
