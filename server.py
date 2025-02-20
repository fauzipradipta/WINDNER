# -*- coding: utf-8 -*-
"""server.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1tiaOb0AEQ9P1sDeUN6ItgjBjGppplXhj
"""

# !pip install websockets

import asyncio
import json
import logging
import websockets
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

SUBMIT = {"city": "", "month": "", "day": ""}
USERS = set()

def submit_event():
  # Restore model
  with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

  # Restore cleaned data
  with open('cleanedData.pkl', 'rb') as f:
    wind_speed_df = pickle.load(f)

  filtered_df = wind_speed_df[[SUBMIT['city'], 'Month', 'Day', 'Year', 'Time']].copy()
  filtered_df = filtered_df[filtered_df['Month'] == SUBMIT['month']]
  filtered_df = filtered_df[filtered_df['Day'] == SUBMIT['day']]

  x = filtered_df.drop(SUBMIT['city'], axis=1)
  y = filtered_df[SUBMIT['city']]

  standardscaler = StandardScaler()
  standardscaler.fit(x)
  x_scale = standardscaler.fit_transform(x)

  model.fit(x_scale, y)

  prediction = sum(model.predict(x_scale))/len(x_scale)
  return json.dumps({"type": "submit", "predictValue": str(prediction)})

async def notify_submit():
    if USERS: # asyncio.wait doesn't accept an empty list
        message = submit_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def register(websocket):
    USERS.add(websocket)

async def unregister(websocket):
    USERS.remove(websocket)

async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        # await websocket.send(square_event())
        # await websocket.send(circle_event())
        async for message in websocket:
            data = json.loads(message)
            print("message action is", data["action"])
            if data["action"] == "submit":
                # SUBMIT["prediction"] = data["prediction"]
                SUBMIT["city"] = data["city"]
                SUBMIT["month"] = data["month"]
                SUBMIT["day"] = data["day"]
                await notify_submit()
            else:
                logging.error("unsupported event: {}", data)
    finally:
        await unregister(websocket)


start_server = websockets.serve(counter, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
