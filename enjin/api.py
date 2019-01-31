import discord
import aiohttp
import asyncio
import json
from random import randint
from .errors import BadRaiderIORequest, BadBlizzardRequest
from .formatters import format_realm
from .raiderio import RaiderIO
from .application import GuildApplication

async def create_applications(session: aiohttp.ClientSession, applist: dict, url: str, session_id: str):
    applications = []

    for data in applist:
        applications.append(await get_application(session, data, url, session_id))

    return applications

async def get_blizzard(session: aiohttp.ClientSession, realm: str, name: str):
    url = "https://api.duckie.cc/character/{}/{}?fields=items".format(realm, name)

    response = await make_request(session, "GET", url)

    if 'status' in response and response['status'] == 'nok':
        raise BadBlizzardRequest(response['reason'])

    return response

async def get_raider_io(session: aiohttp.ClientSession, region: str, realm: str, char_name: str):
    api = "https://raider.io/api/v1/characters/profile?region={}&realm={}&name={}&fields=mythic_plus_scores%2Cgear%2Cguild%2Craid_progression%2Cmythic_plus_best_runs".format(
        region, format_realm(realm), char_name.lower())

    response = await make_request(session, "GET", api)

    if 'error' in response:
        if response['statusCode'] == 400:
            raise BadRaiderIORequest(response['message'])

    return response

async def get_application(session: aiohttp.ClientSession, application: dict, url, session_id: str):
    request = {
        "jsonrpc": "2.0",
        "id": "".join(["%s" % randint(0, 9) for num in range(0, 10)]),
        "params": {
            "domain": url,
            "session_id": session_id,
            "application_id": application['application_id']
        },
        "method": "applications.getApplication"
    }
    response = await enjin_request(session, url, request)

    return GuildApplication(response['result'])

async def get_applications(session: aiohttp.ClientSession, url: str, session_id: str, limit=50):
    request = {
        "jsonrpc": "2.0",
        "id": "".join(["%s" % randint(0, 9) for num in range(0, 10)]),
        "params": {
            "session_id": session_id,
            "application_form_id": 49868267,
            "type": "open",
            "limit": limit
        },
        "method": "applications.getList"
    }
    return await enjin_request(session, url, request)

async def create_session(session: aiohttp.ClientSession, url: str=None, email: str=None, password: str=None):
    request = {
        "jsonrpc": "2.0",
        "id": "".join(["%s" % randint(0, 9) for num in range(0, 10)]),
        "params": {
            "email": email,
            "password": password
        },
        "method": "user.login"
    }
    return await enjin_request(session, url, request)

async def check_session(session: aiohttp.ClientSession, url: str, session_id: str):
    request = {
        "jsonrpc": "2.0",
        "id": "".join(["%s" % randint(0, 9) for num in range(0, 10)]),
        "params": {
            "session_id": session_id
        },
        "method": "User.checkSession"
    }
    return await enjin_request(session, url, request)

async def enjin_request(session: aiohttp.ClientSession, url: str, data: dict):
    return await make_request(session, "POST", url, None, json.dumps(data))

async def make_request(
        session: aiohttp.ClientSession,
        method: str, url: str, headers: dict=None,
        data: dict=None, params: dict=None,
        auth: aiohttp.BasicAuth=None):
    async with session.request(method, url, headers=headers, data=data, params=params, auth=auth, allow_redirects=False) as resp:
        return await resp.json()
