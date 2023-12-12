from threading import Thread
import socket
from time import sleep
from uuid import uuid4
from datetime import datetime
import pandas as pd


class TCP:
    check = True
    """
    Generate random string for the TCP Handshake. 
    Default: Port: 200, Exchange: STU
    """

    def __init__(
        self, port: int = 200, exchange: str = "STU", keep_alive: bool = True
    ) -> None:
        self.name = uuid4()
        self.exchange = exchange
        self.port = port
        self.live_data_raw = {}
        self.data = []
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Thread(target=self.connect).start()
        sleep(2)
        if keep_alive:
            Thread(target=self.keep_alive).start()

    def get(self, isin: str):
        df = pd.DataFrame(self.data)
        df = df[df["isin"] == isin.upper()]
        df.index = pd.DataFrame(pd.to_datetime(df["zeit"]))
        df = df.drop(columns=["zeit", "isin"])
        return df

    def connect(self) -> None:
        sender = f"CI|REV=2.24|NAME={self.name}\n"
        self.s.connect(("127.0.0.1", self.port))
        self.s.send(sender.encode("utf-8"))
        sleep(1)
        while self.check:
            data = self.splitter(self.s.recv(2048).decode("utf-8"))
            data["Antwortzeitpunkt"] = datetime.now().timestamp()
            if data["Antwort"] == "T":
                if data.get("TYPE") in ["BID", "ASK"]:
                    try:
                        isin = data["ISIN"]
                        art = data["TYPE"]
                        zeit = data["TIME"]
                        preis = data["PRICE"]
                        try:
                            if zeit > self.live_data_raw[isin][art]["TIME"]:
                                self.live_data_raw[isin][art]["TIME"] = zeit
                                self.data.append(
                                    {
                                        "isin": isin,
                                        "type": art,
                                        "preis": preis,
                                        "zeit": zeit,
                                    }
                                )
                        except TypeError:
                            pass
                    except KeyError:
                        pass
        self.s.close()

    def send(self, data) -> None:
        self.s.send(data.encode("utf-8"))

    def splitter(self, msg: str) -> dict:
        timer = 0
        for e in msg:
            if e == "|":
                timer += 1
        data = msg.split("|")
        result = {}
        for e in range(timer):
            summe = e + 1
            key = data[summe].split("=")[0]
            try:
                try:
                    if float(data[summe].split("=")[1]):
                        value = float(data[summe].split("=")[1].strip())
                        if "TIME" in key:
                            value = datetime.fromtimestamp(
                                int(data[summe].split("=")[1].strip()) / 1000.0
                            )
                except ValueError:
                    if data[summe].split("=")[1].isdigit():
                        value = int(data[summe].split("=")[1].strip())
                        if "TIME" in key:
                            value = datetime.fromtimestamp(
                                int(data[summe].split("=")[1].strip()) / 1000.0
                            )
                    else:
                        value = data[summe].split("=")[1].strip()
                        if key == "EXCHANGES":
                            datas = [
                                e for e in data[summe].split("=")[1].strip().split(",")
                            ]
                            value = datas
                result[key] = value
            except:
                pass
        result["Antwort"] = data[0]
        return result

    def keep_alive(self):
        while self.check:
            search = f"E|TEXT=keep alive\n"
            self.send(search)
            sleep(120)

    def market_order(self, isin: str, menge: int, direction: str = "BUY") -> dict:
        search = f"AO|ISIN={isin.upper()}|EXCHANGE={self.exchange}|BUYSELL={direction}|SIZE={menge}|LIMIT=0|WITHCOSTS=True\n"
        self.send(search)

    def sub(self, isin: str, mode: str = "ALL") -> dict:
        """Subscription to ISIN. Mode: LTO, ALL, L2, OFF, L1INC, L1DEC, L2INC, L2DEC"""
        search = f"QTS|ISIN={isin.upper()}|EXCHANGE={self.exchange}|MODE={mode}\n"
        self.send(search)
        self.live_data_raw[isin.upper()] = {
            "ASK": {
                "TIME": datetime.now().replace(
                    hour=8, minute=0, second=0, microsecond=0
                )
            },
            "BID": {
                "TIME": datetime.now().replace(
                    hour=8, minute=0, second=0, microsecond=0
                )
            },
        }
        sleep(0.5)

    def close(self) -> None:
        """Sub OFF"""
        self.sub("OFF")
        self.check = False
