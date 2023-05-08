#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import requests, time, sys, argparse, base64, binascii, json, logging, random, os, websocket,threading
from collections import defaultdict
class IQ_WEBSOCKET():
	def __init__(self, iq_api):
		self.iq_api = iq_api
		self.iq_websocket = None
		self.iq_websocket_conectado = False

	def conectar(self):
		self.desconectar_servidor()
		self.iq_websocket = websocket.WebSocketApp("wss://ws-br.iqoption.com/echo/websocket", on_open=self.websocket_open, on_message=self.websocket_mensagem, on_close=self.websocket_fechado)
		#self.iq_websocket = websocket.WebSocketApp("wss://ws.trade.capitalbears.com/echo/websocket", on_open=self.websocket_open, on_message=self.websocket_mensagem, on_close=self.websocket_fechado)
		threading.Thread(target=self.iq_websocket.run_forever, daemon=True).start()

	def websocket_open(self):self.iq_websocket_conectado = True

	def websocket_mensagem(self, mensagem):
		mensagem = mensagem = json.loads(mensagem)
		msg = mensagem['msg']
		name = mensagem['name']
		if "request_id" in mensagem:
			request_id = mensagem['request_id']
		else:
			request_id = False
		""""
		if name != 'heartbeat' and name != 'timeSync' and name != 'candle-generated'  and name != 'candles':
			salvar(name, mensagem)
			print('#################################################################')		
			print(name)		
			print(request_id)		
			print('#################################################################')		
		"""
		if name == "authenticated":
			if msg:	self.iq_api.iq_autenticado = True
		#elif name == 'heartbeat':
		#	self.iq_enviar_mensagem('heartbeat', {'heartbeatTime': msg, 'userTime': round(time.time()*1000)})	
		elif name == 'timeSync':
			self.iq_api.timestamp_iq = msg
		elif name == 'profile':
			self.iq_api.perfil = msg['result']
			registro.info('Bem-Vindo {}! ({})'.format(msg['result']['first_name'], msg['result']['email']))
			self.iq_api.iq_bot.perfil_alterado()
		elif name == 'profile-changed':
			self.iq_api.perfil = msg
			self.iq_api.iq_bot.perfil_alterado()
		elif name == 'balances':
			for saldo in msg:
				self.iq_api.saldo[saldo['type']] = {'id': saldo['id'], 'saldo': saldo['amount'], 'moeda': saldo['currency']} 
				self.iq_api.iq_bot.novo_saldo(saldo['type'])
		elif name == 'balance-changed':
			saldo = msg['current_balance']
			self.iq_api.saldo[saldo['type']]['saldo'] = saldo['amount']
		elif name == "result":
			self.iq_api.requisicoes[request_id] = msg['success']
		elif name == "active-exposure":
			self.iq_api.requisicoes[request_id] = msg
		elif name == "candles":
			self.iq_api.requisicoescandles[request_id] = msg["candles"]
		elif name == "initialization-data":
			self.iq_api.dados_inicializacao_raw = msg
		elif name == "candle-generated":
			self.iq_api.requisicoestickers[str(msg["active_id"])+"_"+str(msg["size"])](msg)
		elif name == 'position-changed':
			#ordem criada
			if msg['status'] == 'open' and ('digital' in msg['instrument_type'] or 'turbo' in msg['instrument_type'] or 'binary' in msg['instrument_type']):
				if'digital' in msg['instrument_type']:
					id_externo = msg['raw_event']['order_ids'][0]
				elif'turbo' or 'binary' in msg['instrument_type']:
					id_externo = msg['external_id']
				
				for order in self.iq_api.requisicoes_ordens:
					if self.iq_api.requisicoes_ordens[order]['id'] == id_externo:
						id = msg['id']
						tipo_ordem = msg['instrument_type'].replace('-option', '')
						par_id = msg['active_id']
						nome_par = self.iq_api.converter_id_para_par(par_id)
						investimento = msg['invest']
						preco_abertura = msg['open_quote']
						hora_abertura = msg['open_time']
						status = msg['status']
						
						if'digital' in msg['instrument_type']:
							id_instrumento = msg['raw_event']['instrument_id']
							direcao = msg['raw_event']['instrument_dir']
							hora_fechamento = int(msg['raw_event']['instrument_timeframe']/1000)
							tipo_conta = msg['raw_event']['user_balance_type']
						elif'turbo' or 'binary' in msg['instrument_type']:
							id_instrumento = msg['instrument_id']
							direcao = msg['raw_event']['direction']
							hora_fechamento = msg['raw_event']['expiration_time']
							tipo_conta = msg['raw_event']['user_balance_type']

						if not id_externo in self.iq_api.ordens:
							self.iq_api.ordens[id_externo] = {
								'id': id,
								'id_externo': id_externo,
								'tipo_ordem': tipo_ordem,
								'par_id': par_id,
								'nome_par': nome_par,
								'investimento': investimento,
								'preco_abertura': preco_abertura,
								'hora_abertura': hora_abertura,
								'status': status,
								'id_instrumento': id_instrumento,
								'direcao': direcao,
								'hora_fechamento': hora_fechamento,
								'tipo_conta': tipo_conta
							}
						break
			# ordem finalizada
			if(msg['status'] == 'closed' or msg['status'] == 'sold') and ('digital' in msg['instrument_type'] or 'turbo' in msg['instrument_type'] or 'binary' in msg['instrument_type']):
				if'digital' in msg['instrument_type']:
					id_externo = msg['raw_event']['order_ids'][0]
				elif'turbo' or 'binary' in msg['instrument_type']:
					id_externo = msg['external_id']
				if id_externo in self.iq_api.ordens:
					self.iq_api.ordens[id_externo]['status'] = msg['status']
					self.iq_api.ordens[id_externo]['preco_fechamento'] = msg['close_quote']
					self.iq_api.ordens[id_externo]['retorno'] = msg['close_profit']
					resultado, lucro = self.iq_api.computar_resultado(self.iq_api.ordens[id_externo])
					self.iq_api.ordens[id_externo]['resultado'] = resultado
					self.iq_api.ordens[id_externo]['lucro'] = lucro


					self.iq_api.iq_bot.ordem_finalizada(self.iq_api.ordens[id_externo])
					
					lastorder = ''
					for order in self.iq_api.requisicoes_ordens:
						lastorder = order
						if self.iq_api.requisicoes_ordens[order]['id'] == id_externo:
							break
					if lastorder != '':
						del self.iq_api.requisicoes_ordens[lastorder]
		elif name == 'option':
			if 'id' in msg:
				self.iq_api.requisicoes_ordens[request_id] = msg
			elif 'message' in msg:
				self.iq_api.requisicoes_ordens[request_id] = {'message': msg['message']}
		elif name == 'digital-option-placed':
			if'id' in msg:
				self.iq_api.requisicoes_ordens[request_id] = msg
			elif'message' in msg:
				self.iq_api.requisicoes_ordens[request_id] = {'message': msg['message']}
		elif name == 'underlying-list':
			self.iq_api.requisicoes['underlying-list'] = msg
		elif name == 'instrument-quotes-generated':
			active = self.iq_api.converter_id_para_par(msg["active"])
			period = msg["timeframe"]["period"]
			self.iq_api.requisicoes['instrument-quotes-generated'] = {}
			self.iq_api.requisicoes['instrument-quotes-generated'][active] = {}
			self.iq_api.requisicoes['instrument-quotes-generated'][active][period] = {}
			ans = {}
			for data in msg["quotes"]:
				# FROM IQ OPTION SOURCE CODE
				if data["price"]["ask"] == None:
					ProfitPercent = None
				else:
					askPrice = (float)(data["price"]["ask"])
					ProfitPercent = ((100-askPrice)*100)/askPrice
				for symble in data["symbols"]:
					try:
						ans[symble] = ProfitPercent
					except:
						pass
			self.iq_api.requisicoes['instrument-quotes-generated'][active][period] = ans
		else:
			if request_id:
				self.iq_api.requisicoes[request_id] = msg
			else:
				self.iq_api.requisicoes[name] = msg

	def websocket_fechado(self, cliente, codigo, mensagem):
		self.iq_websocket_conectado = False
		self.iq_api.iq_autenticado = False
		registro.info(
			"Conexão com a Capital Bear encerrada {}".format(mensagem))

	def desconectar_servidor(self):
		try:
			self.iq_websocket.close()
		except:
			pass
	
	def iq_enviar_mensagem(self, name, msg, request_id=None):
		if request_id is None:
			request_id = "".join(random.choices('abcdef0123456789', k=6))
		self.iq_websocket.send(json.dumps({"msg": msg, "name": name, "request_id": str(request_id)}))
		return request_id
class IQ_API():
	
	def __init__(self, iq_bot, email, password, ssid):
		self.iq_bot = iq_bot
		self.email = email
		self.password = password
		self.ssid = ssid
		self.iq_autenticado = False
		self.perfil = None
		self.grupo_id = None
		self.timestamp_iq = None
		self.requisicoes = {}
		self.requisicoescandles = {}
		self.requisicoestickers = {}
		self.dados_inicializacao_raw = {}
		self.saldo = {}
		self.ordens = {}
		self.requisicoes_ordens = {}
		self.OPEN_TIME = nested_dict(3, dict)
		self.iq_websocket = IQ_WEBSOCKET(self)

	def logar(self, email, password):
		cookies = {"platform": "15", "device_id": "".join(random.choices("abcdef0123456789", k=32))}
		headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36"}
		data = {"identifier": email, "password": password}
		try:
			resposta = requests.post("https://auth.iqoption.com/api/v2/login",headers=headers, data=data, cookies=cookies, timeout=10).json()
			if "ssid" in resposta:
				#salvar_config('ssid', resposta["ssid"])
				return True, resposta["ssid"]
			elif "code" in resposta:
				return False, resposta["code"]
			else:
				return False, None
		except Exception as e:
			return False, getattr(e, "message", repr(e))
	
	def conectar(self):
		if not self.ssid:
			login_status, login_resposta = self.logar(self.email, self.password)
			if not login_status:
				return False, login_resposta
			self.ssid = login_resposta
			#salvar_config('ssid', self.ssid)
		self.iq_websocket.conectar()
		inicio = time.time()
		while 1:
			if self.iq_websocket.iq_websocket_conectado:
				break
			if time.time()-inicio > 10:
				return False, 'websocket_not_connected'
			time.sleep(0.1)
		self.iq_websocket.iq_enviar_mensagem('authenticate', {'protocol': 3, 'ssid': self.ssid})
		inicio = time.time()
		while 1:
			if self.iq_autenticado:
				break
			if time.time()-inicio > 10 or not self.iq_websocket.iq_websocket_conectado:
				return False, 'authentication_failed'
			time.sleep(0.1)
		self.iq_inscrever_essencial()
		self.obter_dados_inicializacao()
		inicio = time.time()
		while 1:
			if self.perfil and self.saldo:
				break
			if time.time()-inicio > 10:
				return False, 'profile_or_balance_not_received'
			time.sleep(0.1)
		return True, None
	
	def iq_inscrever_essencial(self): 
		self.iq_websocket.iq_enviar_mensagem('sendMessage', {'name': 'core.get-profile'}); 
		self.iq_websocket.iq_enviar_mensagem('sendMessage', {'name': 'get-balances'}); 
		self.iq_websocket.iq_enviar_mensagem('subscribeMessage', {'name': 'profile-changed'}); 
		self.iq_websocket.iq_enviar_mensagem('subscribeMessage', {'name': 'internal-billing.balance-changed'}); 
		self.iq_websocket.iq_enviar_mensagem('subscribeMessage', {'name': 'portfolio.position-changed'}); 
		self.iq_websocket.iq_enviar_mensagem('sendMessage', {'name': 'set-transport-state', 'body': {'transport': 'email', 'enabled': False}})

	def get_digital_current_profit(self, par, timeframe):
		profit = self.requisicoes['instrument-quotes-generated'][par][timeframe * 60]
		for key in profit:
			if key.find("SPT") != -1:
				return profit[key]
		return False

	def subscribe_strike_list(self, par, timeframe):
		self.iq_websocket.iq_enviar_mensagem('subscribeMessage', {
            "name": "instrument-quotes-generated",
            "params": {
                "routingFilters": {
                    "active": self.converter_par_para_id(par),
                    "expiration_period": timeframe*60,
                    "kind": "digital-option",
                },
            },
            "version": "1.0"
        })
	
	def unsubscribe_strike_list(self, par, timeframe):
		self.iq_websocket.iq_enviar_mensagem('unsubscribeMessage', {
            "name": "instrument-quotes-generated",
            "params": {
                "routingFilters": {
                    "active": self.converter_par_para_id(par),
                    "expiration_period": timeframe*60,
                    "kind": "digital-option",
                },
            },
            "version": "1.0"
        })

	def iq_obter_essencial(self):
		self.iq_websocket.iq_enviar_mensagem("setOptions", {"sendResults": True})

	def obter_dados_inicializacao(self):
		self.dados_inicializacao_raw = {}
		self.iq_websocket.iq_enviar_mensagem("sendMessage", {"name": "get-initialization-data", "version": "3.0", "body": {}})
		inicio = time.time()
		while 1:
			if self.dados_inicializacao_raw:
				self.pares = {}
				for tipo_mercado in ["binary", "turbo"]:
					for par in self.dados_inicializacao_raw[tipo_mercado]["actives"]:
						nome = self.dados_inicializacao_raw[tipo_mercado]["actives"][par]["name"].replace(
							"front.", "")
						if not int(par) in self.pares:
							self.pares[int(par)] = {"nome": nome}
						ativo = self.dados_inicializacao_raw[tipo_mercado]["actives"][par]["enabled"]
						suspenso = self.dados_inicializacao_raw[tipo_mercado]["actives"][par]["is_suspended"]
						self.pares[int(par)][tipo_mercado] = {
							"ativo": ativo, "suspenso": suspenso}
				return True
			if time.time() - inicio > 5 or not self.iq_websocket.iq_websocket_conectado:
				registro.info("Sem resposta do servidor, não foi possivel obter dados de iniciação")
				return False
			time.sleep(0.1)

	def get_candles(self, par, interval, count, endtime):
		#registro.info("Obtendo lista de velas {} em tempo real".format(par))
		msg = {"name": "get-candles",
			   "version": "2.0",
			   "body": {
				   "active_id": self.converter_par_para_id(par),
				   "split_normalization": True,
				   "size": interval,  # time size sample:if interval set 1 mean get time 0~1 candle
				   # int(self.api.timesync.server_timestamp),
				   "to": int(endtime),
				   "count": count,
				   "only_closed": True
			   }
			   }
		request_id = self.iq_websocket.iq_enviar_mensagem("sendMessage", msg)
		inicio = time.time()
		while 1:
			if time.time() - inicio >= 30:
				registro.info("Sem resposta do servidor, não foi possivel obter velas do par {}".format(par))
				return []
			if request_id in self.requisicoescandles:
				ret = self.requisicoescandles[request_id]
				del self.requisicoescandles[request_id]
				return ret
			time.sleep(.1)
	
	def get_active_exposure(self, par, expiracao, option):
		timestamp = int(self.timestamp_iq/1000)
		if expiracao == 1:
			exp, _ = get_expiration_time(timestamp, expiracao)
		else:
			now_date = datetime.fromtimestamp(timestamp) + timedelta(minutes=1, seconds=30)
			while True:
				if now_date.minute % expiracao == 0 and time.mktime(now_date.timetuple()) - timestamp > 30:
					break
				now_date = now_date + timedelta(minutes=1)
			exp = time.mktime(now_date.timetuple())
		msg = {"name": "get-active-exposure",
               "version": "1.0",
               "body": {
                        "active_id": self.converter_par_para_id(par),
                        "currency": self.perfil['currency'],
                        "instrument_type": ("digital-option" if option == 1 else "binary-option" if expiracao>=15 else "turbo-option"),
                        "time": int(exp)
                    }
               } 
		request_id = self.iq_websocket.iq_enviar_mensagem("sendMessage", msg)
		inicio = time.time()
		while 1:
			if time.time() - inicio >= 30:
				registro.info("Sem resposta do servidor, não foi possivel obter informações do par {}".format(par))
				return []
			if request_id in self.requisicoes:
				ret = self.requisicoes[request_id]
				del self.requisicoes[request_id]
				return ret
			time.sleep(.1)
	
	def inscrever_obter_velas(self, par, periodo, ticker):
		#registro.info("Obtendo velas {} em tempo real".format(par))
		idpar = self.converter_par_para_id(par)
		request_id = self.iq_websocket.iq_enviar_mensagem("subscribeMessage", {
														  "name": "candle-generated", "params": {"routingFilters": {"active_id": idpar, "size": periodo}}})
		self.requisicoestickers[str(idpar)+"_"+str(periodo)] = ticker

	def desinscrever_obter_velas(self, par, periodo):
		registro.info("Parando velas {} em tempo real".format(par))
		request_id = self.iq_websocket.iq_enviar_mensagem("unsubscribeMessage", {"name": "candle-generated", "params": {
														  "routingFilters": {"active_id": self.converter_par_para_id(par), "size": periodo}}})
		inicio = time.time()
		while 1:
			if time.time() - inicio >= 5:
				registro.info(
					"Sem resposta do servidor, não foi possivel parar de obter velas do par {}".format(par))
				return False
			if request_id in self.requisicoes:
				del self.requisicoes[request_id]
				return True
			time.sleep(.1)

	def converter_par_para_id(self, par):
		for id in self.pares:
			if self.pares[id]["nome"] == par:
				return id
		return False
	
	def converter_id_para_par(self, id):
		try:
			return self.pares[id]["nome"]
		except:
			return id
	
	def obter_sessions(self):
		self.iq_websocket.iq_enviar_mensagem('sendMessage',	{'name': 'get-sessions'})

	def computar_resultado(self, aposta):
		if aposta['retorno'] > aposta['investimento']:
			resultado = 'ganhou'
		elif aposta['retorno'] < aposta['investimento']:
			resultado = 'perdeu'
		else:
			resultado = 'empate'
		return resultado, round(aposta['retorno']-aposta['investimento'], 2)

	def valor_do_saldo(self, tipo_id): return self.saldo[tipo_id]['saldo']
	
	def id_do_saldo(self, tipo_id): return self.saldo[tipo_id]['id']

	def tipo_saldo(self, tipo_id):
		if tipo_id == 1:
			return'real'
		elif tipo_id == 4:
			return'demo'
		return None
	
	def enviar_aposta_binaria_turbo_raw(self, id_par, direcao, expiracao, valor, tipo_ordem, tipo_conta):
		request_id = self.iq_websocket.iq_enviar_mensagem('sendMessage', {
			'name': 'binary-options.open-option', 
			'version': '1.0', 
			'body': {
				'user_balance_id': tipo_conta, 
				'active_id': id_par, 
				'option_type_id': tipo_ordem, 
				'direction': direcao, 
				'expired': expiracao, 
				'price': valor}
			})
		return True, request_id
		
	def enviar_aposta_digital_raw(self, id_par, instrument_id, valor, tipo_conta):
		request_id = str(round(time.time()*1000))
		self.iq_websocket.iq_enviar_mensagem('sendMessage', {
			'name': 'digital-options.place-digital-option', 
			'version': '2.0', 
			'body': {
				'user_balance_id': tipo_conta, 
				'instrument_id': instrument_id, 
				'amount': str(valor), 
				'instrument_index': 0, 
				'asset_id': id_par
				}
			}, request_id)
		return True, request_id

	def get_all_open_time(self, option): #digital = 1 binario = 2
		# all pairs openned
		self.OPEN_TIME = nested_dict(3, dict)
		if option == 2 or option == 0:
			binary = threading.Thread(target=self.__get_binary_open)
			binary.start()
		if option == 1 or option == 0:
			digital = threading.Thread(target=self.__get_digital_open)
			digital.start() 
		if option == 2 or option == 0:
			binary.join() 
		if option == 1 or option == 0:
			digital.join()
		return self.OPEN_TIME

	def __get_binary_open(self):
		# for turbo and binary pairs
		binary_data = self.get_all_init_v2()
		binary_list = ["binary", "turbo"]
		if binary_data:
			for option in binary_list:
				if option in binary_data:
					for actives_id in binary_data[option]["actives"]:
						active = binary_data[option]["actives"][actives_id]
						name = str(active["name"]).split(".")[1]
						if active["enabled"] == True:
							if active["is_suspended"] == True:
								self.OPEN_TIME[option][name] = False
							else:
								self.OPEN_TIME[option][name] = True
						else:
							self.OPEN_TIME[option][name] = active["enabled"]    

	def __get_digital_open(self):
		# for digital options
		digital_data = self.get_digital_underlying_list_data()
		for digital in digital_data:
			name = digital["underlying"]
			schedule = digital["schedule"]
			self.OPEN_TIME["digital"][name] = False
			for schedule_time in schedule:
				start = schedule_time["open"]
				end = schedule_time["close"]
				if start < time.time() < end:
					self.OPEN_TIME["digital"][name] = True

	def get_digital_underlying_list_data(self):
		request_id = self.iq_websocket.iq_enviar_mensagem('sendMessage', {"name": "get-underlying-list", "version": "2.0", "body": {"type": "digital-option"}})
		start_t = time.time()
		self.requisicoes['underlying-list'] = None
		while 1:
			if time.time() - start_t >= 30:
				logging.error('**warning** get_digital_underlying_list_data late 30 sec')
				return None
			if  self.requisicoes['underlying-list'] is not None:
				ret = self.requisicoes['underlying-list']
				del self.requisicoes['underlying-list']
				return ret["underlying"]

	def get_all_init_v2(self):
		self.dados_inicializacao_raw = None
		self.iq_websocket.iq_enviar_mensagem('sendMessage', {"name": "get-initialization-data",	"version": "3.0","body": {}}); 
		start_t = time.time()
		while self.dados_inicializacao_raw == None:
			if time.time() - start_t >= 30:
				logging.error('**warning** get_all_init_v2 late 30 sec')
				return None
		return self.dados_inicializacao_raw

	def get_all_init(self):
		request_id = self.iq_websocket.iq_enviar_mensagem('api_option_init_all', {}); 
		inicio = time.time()			
		while 1:
			if time.time() - inicio >= 30:
				registro.info("Sem resposta do servidor, não foi possivel obter init_all.")
				return []
			if request_id in self.requisicoes:
				ret = self.requisicoes[request_id]
				del self.requisicoes[request_id]			
				return ret
			time.sleep(.1)

	def get_all_profit(self):
		all_profit = nested_dict(2, dict)
		init_info = self.get_all_init()
		for actives in init_info["result"]["turbo"]["actives"]:
			name = init_info["result"]["turbo"]["actives"][actives]["name"]
			name = name[name.index(".") + 1:len(name)]
			all_profit[name]["turbo"] = (
				100.0 -
				init_info["result"]["turbo"]["actives"][actives]["option"]["profit"][
					"commission"]) / 100.0

		for actives in init_info["result"]["binary"]["actives"]:
			name = init_info["result"]["binary"]["actives"][actives]["name"]
			name = name[name.index(".") + 1:len(name)]
			all_profit[name]["binary"] = (
				100.0 -
				init_info["result"]["binary"]["actives"][actives]["option"]["profit"][
					"commission"]) / 100.0
		return all_profit
	
	def change_balance(self, tipo):
		if tipo == 'REAL':
			self.iq_bot.tipo_id = 1
		if tipo == 'PRACTICE':
			self.iq_bot.tipo_id = 4

	def confere_aposta(self, request_id, position):
		inicio = time.time()
		while 1:
			if request_id in self.requisicoes_ordens:
				if'id' in self.requisicoes_ordens[request_id]:
					id = self.requisicoes_ordens[request_id]['id']
					if id in self.ordens:
						self.iq_bot.nova_ordem(self.ordens[id], position)
						#del self.requisicoes_ordens[request_id]
						return True, id
				elif'message' in self.requisicoes_ordens[request_id]:
					message = self.requisicoes_ordens[request_id]['message']
					del self.requisicoes_ordens[request_id]
					registro.info('Erro ao abrir ordem: {}'.format(message))
					return False, message
			if time.time()-inicio >= 10:
				registro.info('Sem resposta do servidor, Verifique se sua ordem foi executada.')
				return False, ''
			time.sleep(.1)
class IQ_BOT():
	def __init__(self, email, password, ssid):
		global entrada, option, meta
		self.email = email
		self.password = password
		self.ssid = ssid
		self.vitorias = 0
		self.derrotas = 0
		self.empates = 0
		self.lucro = 0
		self.tipo_id = 4 # PRACTICE
		self.option = option #digital = 1 binary = 2
		self.meta = meta
		self.iq_api = IQ_API(self, email, password, ssid)
		self.emAnalize = True

		self.vitoriasImpedidas = 0
		self.vitoriasEmSequencia = 0
		self.perdido = 0
		self.perdasImpedidas = 0
		self.perdasEmSequencia = 0
		
		self.sorosUsado = 0
		self.sorosGanho = 0
		
		self.sorosGaleUsado = 0
		self.sorosGaleGanho = 0
		self.sorosGalePerdido = 0

		self.vRentrada = entrada

	def conectar(self):
		status, razao = self.iq_api.conectar()
		if status:
			#registro.info('Conexão bem sucedida.')
			return True
		else:
			if'authentication_failed' in razao:
				self.iq_api.ssid = None
				status, razao = self.iq_api.conectar()
				if status:
					registro.info('Conexão bem sucedida.')
					return True
			registro.info(
				'Ocorreu um erro ao conectar, {}'.format(razao))
			return False
	
	def novo_saldo(self, tipo_id):
		if tipo_id == 1:
			valor = self.iq_api.saldo[tipo_id]['saldo']
			tipo = 'real'
			moeda = self.iq_api.saldo[tipo_id]['moeda']
			if self.meta > 0 and valor >= meta:
				registro.info('Meta de saldo atingida.')
				if balance == 'REAL':
					self.iq_api.change_balance('PRACTICE') 
					balance = 'PRACTICE'
			

		elif tipo_id == 4:
			valor = self.iq_api.saldo[tipo_id]['saldo']
			tipo = 'demo'
			moeda = self.iq_api.saldo[tipo_id]['moeda']

	def perfil_alterado(self):
		if self.iq_api.perfil['group_id'] != self.iq_api.grupo_id:
			self.iq_api.grupo_id = self.iq_api.perfil['group_id']
			if self.iq_api.grupo_id == 18:
				registro.info('Conta Limitada')

	def nova_ordem(self, aposta, position):
		string = "→ "+(self.iq_api.converter_id_para_par(aposta['par_id'])).ljust(10, ' ')+" "
		if aposta['direcao'] == 'put':
			string += c.rd+"▼"+c.rs
			string += ' '+str(position).ljust(8," ")
			string += ' → '+str(aposta['preco_abertura']).rjust(8," ")
			if aposta['preco_abertura']>=position:
				string += c.gr+" Perfeita ".ljust(10," ")+c.rs
				string += "{:06f}".format((aposta['preco_abertura']-position)).ljust(8," ")
			else:
				string += c.rd+" Delay ".ljust(10," ")+c.rs
				string += "{:06f}".format((position-aposta['preco_abertura'])).ljust(8," ")
		else:
			string += c.gr+"▲"+c.rs
			string += ' '+str(position).ljust(8," ")
			string += ' → '+str(aposta['preco_abertura']).rjust(8," ")

			if aposta['preco_abertura']<=position:
				string += c.gr+" Perfeita ".ljust(10," ")+c.rs
				string += "{:06f}".format((position-aposta['preco_abertura'])).ljust(8," ")
			else:
				string += c.rd+" Delay ".ljust(10," ")+c.rs
				string += "{:06f}".format((aposta['preco_abertura']-position)).ljust(8," ")

		string += " $"+(real_br_money_mask(aposta['investimento']).rjust(13," "))
		registro.info(string)

	def ordem_finalizada(self, aposta):
		global balance,sorosGale,sorosGalefator,sorosGaleLimite,soros,sorosFator,limiteDeLoss,WinsParaRetorno,porcentagem
		msg = ''
		msgBandeira = ''
		if aposta['resultado'] == 'ganhou':
			self.vitorias += 1
		elif aposta['resultado'] == 'perdeu':
			self.derrotas += 1
		elif aposta['resultado'] == 'empate':
			self.empates += 1
		del self.iq_api.ordens[aposta['id_externo']]
		
		valor = aposta['lucro']
		#Se tiver perdido em sequencia e estiver em analise.
		if self.emAnalize:
			if valor > 0:
				self.vitoriasImpedidas += 1
				self.vitoriasEmSequencia += 1
				if self.vitoriasEmSequencia>=WinsParaRetorno:
					self.emAnalize = False
					if balance == 'REAL':
						iq_bot.iq_api.change_balance('REAL') 
					msg = "Análise concluída.".ljust(40," ")
				else:
					msg = "Vitória, aguardando análise.".ljust(40," ")
				msgBandeira = c.On_Yellow+" WIN  "+c.rs+" "
			# perdeu
			else:
				self.perdasImpedidas += 1
				self.vitoriasEmSequencia=0
				msg = "Em análise.".ljust(40," ")
				msgBandeira = c.On_Yellow+" LOSS "+c.rs+" "
		else:
			self.lucro += round(valor, 2)
			if valor == 0:
				msg = 'Empate.'
				# Reinicia Soros
				self.sorosUsado = 0
			# WIN!!! ;)
			elif valor > 0:
				self.perdasEmSequencia = 0
				self.perdido += valor
				if self.perdido > 0:
					self.perdido = 0
				msg = "".ljust(40," ")
			
				# Se recuperacao sorosGale estiver ativa 
				if sorosGale > 0 and self.sorosGalePerdido < 0:
					self.sorosGaleGanho += 1
					#Aplica sorosGale a quantidade de vezes informada
					if self.sorosGaleGanho < sorosGale:
						self.vRentrada = ((abs(self.sorosGalePerdido)/(85/100))/sorosGale)*sorosGalefator
						#self.vRentrada = ((abs(self.sorosGalePerdido)/(payout/100))/sorosGale)*sorosGalefator
						msg = "sorosGale aplicada.".ljust(40," ")
					#Conclui a recuperacao sorosGale se já ganhou todas as vezes.
					else:
						self.sorosGaleUsado = 0
						self.sorosGaleGanho = 0
						self.sorosGalePerdido = 0
						self.vRentrada = entrada
						msg = "sorosGale finalizada.".ljust(40," ")
				else:
					self.sorosGaleGanho = 0
					# Se tiver ativado soros
					if soros > 0:
						# se o ciclo de soros nao estiver completo
						if self.sorosUsado < soros:
							self.sorosGanho += valor
							self.sorosUsado += 1
							self.vRentrada = entrada + (self.sorosGanho * sorosFator)
							msg = "Aplicando soros.".ljust(40," ")
						else:
							self.sorosGanho = 0
							self.sorosUsado = 0
							self.vRentrada = entrada
							msg = "Último nível de soros.".ljust(40," ")
				msgBandeira = c.On_Green+" WIN  "+c.rs+" "
			# LOSS :(
			else:
				self.vitoriasEmSequencia=0
				msg = "".ljust(40," ")
				self.perdasEmSequencia += 1
				if self.perdasEmSequencia>=limiteDeLoss:
					self.emAnalize = True
				self.perdido += valor
				# reinicia soros
				self.sorosUsado = 0
				# sorosGale
				if sorosGale > 0:
					self.sorosGaleGanho = 0
					self.sorosGalePerdido += valor
					#Aplica valor de recuperacao
					if self.sorosGaleUsado <= sorosGaleLimite:
						self.vRentrada = ((abs(self.sorosGalePerdido)/(85/100))/sorosGale)*sorosGalefator
						self.sorosGaleUsado += 1
						msg = "Aplicado sorosGale.".ljust(40," ")
					else:
						self.sorosGaleUsado = 0
						self.sorosGalePerdido = 0
						self.vRentrada = entrada
						msg = "Limite sorosGale atingido.".ljust(40," ")
				msgBandeira = c.On_Red+" LOSS "+c.rs+" "
		""""
		if porcentagem > 0:		
			print(" → ", real_br_money_mask(porcentagem).rjust(10," "),"%",sep="", end="")
		else:
			print(" → $", real_br_money_mask(self.vRentrada).rjust(10," "),sep="", end="")
		"""
		msg += " $" + (c.BCyan if iq_bot.lucro >= 0 else c.BRed) + real_br_money_mask(iq_bot.lucro).rjust(13," ")+c.rs
		
		if not self.iq_api.ordens:
			registro.info('{} {}X{} {}'.format(msgBandeira, self.vitorias, self.derrotas, msg))

	def novo_ssid(self, sessao):
		self.iq_api.ssid = sessao['id']

	def enviar_ordem(self, par, entrada, dir, timeframe, position):
		timestamp = int(self.iq_api.timestamp_iq/1000)
		exp, idx = get_expiration_time(timestamp, timeframe)
		
		active_id = self.iq_api.converter_par_para_id(par)
		saldo_id = self.iq_api.id_do_saldo(self.tipo_id)
		
		# se for binaria
		if self.option == 2:
			option_type_id = 3 if idx < 5 else 1
			
			status, request_id = iq_bot.iq_api.enviar_aposta_binaria_turbo_raw(active_id, dir, int(exp), entrada, option_type_id, saldo_id)
		# se for digital
		elif self.option == 1:
			date_formated = str(datetime.utcfromtimestamp(exp).strftime("%Y%m%d%H%M"))
			dir = 'P' if dir == 'put' else 'C'
			instrument_id = "do" + str(active_id) + "A" + date_formated[:8] + "D" + date_formated[8:] + \
            "00T" + str(timeframe) + "M" + dir + "SPT"

			status, request_id = iq_bot.iq_api.enviar_aposta_digital_raw(active_id, instrument_id, entrada, saldo_id)
		
		if not status:
			registro.info('Erro ao abrir ordem: {}'.format(id))
		else:
			threading.Thread(target=iq_bot.iq_api.confere_aposta, args=[request_id, position]).start()
			return status
class c:
	gr		  =   '\033[92m' #GREEN
	ye		  =   '\033[93m' #YELLOW
	rd		  =   '\033[91m'  #RED
	bl		  =   "\033[34m"
	rs		  =   '\033[0m' #RESET COLOR
	On_Black	=   "\033[40m"	   # Black
	On_Red	  =   "\033[41m"		 # Red
	On_Green	=   "\033[42m"	   # Green
	On_Yellow   =   "\033[43m"	  # Yellow
	On_Blue	 =   "\033[44m"		# Blue
	On_Purple   =   "\033[45m"	  # Purple
	On_Cyan	 =   "\033[46m"		# Cyan
	On_White	=   "\033[47m"	   # White
	# Bold
	BBlack="\033[1;30m"	   # Black
	BRed="\033[1;31m"		 # Red
	BGreen="\033[1;32m"	   # Green
	BYellow="\033[1;33m"	  # Yellow
	BBlue="\033[1;34m"		# Blue
	BPurple="\033[1;35m"	  # Purple
	BCyan="\033[1;36m"		# Cyan
	BWhite="\033[1;37m"	   # White
def salvar(name, string):
	file1 = open('msgs/'+name+".json","w") 
	file1.write(str(string)) 
	file1.close() 
def nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n - 1, type))
def date_to_timestamp(dt):
    # local timezone to timestamp support python2 pytohn3
    return time.mktime(dt.timetuple())
def get_expiration_time(timestamp, duration):
	now_date = datetime.fromtimestamp(timestamp)
	exp_date = now_date.replace(second=0, microsecond=0)
	if (int(date_to_timestamp(exp_date+timedelta(minutes=1)))-timestamp) > 30:
		exp_date = exp_date+timedelta(minutes=1)
	else:
		exp_date = exp_date+timedelta(minutes=2)
	exp = []
	for _ in range(5):
		exp.append(date_to_timestamp(exp_date))
		exp_date = exp_date+timedelta(minutes=1)

	idx = 50
	index = 0
	now_date = datetime.fromtimestamp(timestamp)
	exp_date = now_date.replace(second=0, microsecond=0)
	while index < idx:
		if int(exp_date.strftime("%M")) % 15 == 0 and (int(date_to_timestamp(exp_date))-int(timestamp)) > 60*5:
			exp.append(date_to_timestamp(exp_date))
			index = index+1
		exp_date = exp_date+timedelta(minutes=1)

	remaning = []

	for t in exp:
		remaning.append(int(t)-int(time.time()))

	close = [abs(x-60*duration) for x in remaning]

	return int(exp[close.index(min(close))]), int(close.index(min(close)))
def get_remaning_time(timestamp):
    now_date = datetime.fromtimestamp(timestamp)
    exp_date = now_date.replace(second=0, microsecond=0)
    if (int(date_to_timestamp(exp_date+timedelta(minutes=1)))-timestamp) > 30:
        exp_date = exp_date+timedelta(minutes=1)

    else:
        exp_date = exp_date+timedelta(minutes=2)
    exp = []
    for _ in range(5):
        exp.append(date_to_timestamp(exp_date))
        exp_date = exp_date+timedelta(minutes=1)
    idx = 11
    index = 0
    now_date = datetime.fromtimestamp(timestamp)
    exp_date = now_date.replace(second=0, microsecond=0)
    while index < idx:
        if int(exp_date.strftime("%M")) % 15 == 0 and (int(date_to_timestamp(exp_date))-int(timestamp)) > 60*5:
            exp.append(date_to_timestamp(exp_date))
            index = index+1
        exp_date = exp_date+timedelta(minutes=1)

    remaning = []

    for idx, t in enumerate(exp):
        if idx >= 5:
            dr = 15*(idx-4)
        else:
            dr = idx+1
        remaning.append((dr, int(t)-int(time.time())))

    return remaning
def calcular_valor_da_aposta(investimento, saldo_operador, saldo_cliente):
	porcentagem_banca = investimento/saldo_operador
	valor_da_aposta = saldo_cliente*porcentagem_banca
	if valor_da_aposta < 2:
		valor_da_aposta = 2
	elif valor_da_aposta > 20000:
		valor_da_aposta = 20000
	return valor_da_aposta
def stampToDate(x, formato):
	return datetime.fromtimestamp(int(x)).strftime(formato)
def now(formato):
	return datetime.now().strftime(formato)
def real_br_money_mask(my_value):
	a = '{:,.2f}'.format(float(my_value))
	b = a.replace(',','v')
	c = b.replace('.',',')
	return c.replace('v','.')
def getdata(days, timeframe):
	url = 'http://bots.fator.cash/integration/candles/?days=' + \
		str(days)+'&timeframe='+str(timeframe)
	r = requests.get(url)
	return r.json()
def getminutos():
	agora = datetime.now()
	inicio = datetime.strptime(agora.strftime(
		'%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
	return int((agora - inicio).total_seconds()/60)
def vertime(vtime):
	if vtime < 0:
		#sys.exit()
		return True
def stopgain(lucro, gain):
	if lucro >= float(abs(gain)):
		time.sleep(2)
		print("Finalizado com vitória. Stop Gain.")
		sys.exit()
def stoploss(lucro, loss):
	if lucro <= float('-' + str(abs(loss))):
		time.sleep(2)
		print("Finalizado com perdas. Stop Loss.")
		sys.exit()
def stoptime(stop_time):
	if(stop_time <= datetime.now()):
		time.sleep(2)
		print("Acabou o tempo de execução.")
		time.sleep(1)
		if iq_bot.lucro > 0:
			print("Finalizado com ganhos.")
		else:
			print("Finalizado com perdas.")
		sys.exit()
def getpayout(par, timeframe, option):
	#digital = 1 binario = 2
	if option == 2:
		a = iq_bot.iq_api.get_all_profit()
		vpar = 0
		if timeframe < 15:
			if 'turbo' in a[par]:
				vpar = a[par]['turbo']
		else:
			if 'binary' in a[par]:
				vpar = a[par]['binary']
		return int(100 * vpar)

	elif option == 1:
		iq_bot.iq_api.subscribe_strike_list(par, timeframe)
		vtime = 10
		ret = 0
		while True:
			vtime = vtime - 1
			if vertime(vtime):
				break
			time.sleep(1)
			d = iq_bot.iq_api.get_digital_current_profit(par, timeframe)
			if d != False:
				ret = int(d)
				break
		iq_bot.iq_api.unsubscribe_strike_list(par, timeframe)
		return ret
def bestpayout(par, timeframe, option):
	payoutbinary = 0
	payoutdigital = 0
	opentime = iq_bot.iq_api.get_all_open_time(option)
	#digital = 1 binario = 2
	if opentime["digital"][par]:
		if option == 0 or option == 1:
			payoutdigital = getpayout(par, timeframe, 1)
	if option == 0 or option == 2:
		if timeframe < 15:
			if opentime["turbo"][par]:
				payoutbinary = getpayout(par, timeframe, 2)
		else:
			if opentime["binary"][par]:
				payoutbinary = getpayout(par, timeframe, 2)
	
	if payoutdigital > payoutbinary:
		openoption = 1
		payout = payoutdigital
	else:
		openoption = 2
		payout = payoutbinary
	#time.sleep(1)
	# verifica se está aberto
	if openoption == 1:
		if not opentime["digital"][par]:
			openoption = -1
	else:
		if timeframe < 15:
			if not opentime["turbo"][par]:
				openoption = -1
		else:
			if not opentime["binary"][par]:

				openoption = -1
	#time.sleep(1)
	# Verifica payout minimo
	if payout < payoutmin:
		openoption = -1
	return openoption, payout
def allopen(option):
	global timeframe
	if option == 2:
		if timeframe > 5:
			opentime = iq_bot.iq_api.get_all_open_time(option)["binary"]
		else:
			opentime = iq_bot.iq_api.get_all_open_time(option)["turbo"]
	else:
		opentime = iq_bot.iq_api.get_all_open_time(option)["digital"]
	return opentime
def sma(velas):
	vm = 0
	for i in range(len(velas)):
		v = velas[i]
		vm = vm + v['close']
	return (vm/len(velas))
def S_engolfo(vls):
	#return True
	atual = vls[1]
	anterior = vls[0]

	atual["topo"] = atual["close"] if atual["close"]>atual["open"] else atual["open"]
	atual["base"] = atual["close"] if atual["close"]<atual["open"] else atual["open"]
	
	anterior["topo"] = anterior["close"] if anterior["close"]>anterior["open"] else anterior["open"]
	anterior["base"] = anterior["close"] if anterior["close"]<anterior["open"] else anterior["open"]
	
	if atual["topo"] <= anterior["topo"] and atual["base"] >= anterior["base"]:		
		return True
	return False	
def S_passareto():
	return True
def S_fechoudentro(vls):
	global debug
	atual = vls[1]
	anterior = vls[0]
	if atual["close"] < anterior["max"] and atual["close"] > anterior["min"]:		
		return True
	return False
def sincronizaSegundos(maiorque, menorque):
	global debug
	while True:
		sincroniza = segundos()
		if debug:
			print("\r", now('%H:%M:%S'), "", end="", sep="")
		#Começa a processar sinal na entrada.
		if(sincroniza > maiorque and sincroniza < menorque):
			break
		else:
			time.sleep(1)
def segundos():
	return int(now('%S'))
def compra(par, entrada, dir, timeframe, position):
	#ajusta preco e faz a compra
	global maxput, maxcall, porcentagem

	#Porcentagem do saldo
	if porcentagem>0:
		entrada = iq_bot.iq_api.valor_do_saldo(iq_bot.tipo_id)*porcentagem/100

	# verifica se está maior que o maximo permitido.
	if dir == 'put':
		entrada  = (maxput-2) if entrada >= maxput else entrada
	else:
		entrada  = (maxcall-2) if entrada >= maxcall else entrada
  
	# verifica se está maior que o mínimo
	entrada = 2 if entrada<2 else entrada

	#envia ordem para o bot
	iq_bot.enviar_ordem(par, entrada, dir, timeframe, position)
def calculaAssertividade(wins, loss):
	if wins+loss == 0:
		return 0
	return round((100/(wins+loss)*wins),2)
def catalogando():
	global debug, timeframe
	casas = '.6f'
	if debug:
		print(c.rs)
		print(c.BYellow, "Catalogando ", par, "...", c.rs, sep="")
		print(c.rs)
		print("# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #")
		print("")
	#zera variáveis
	velas = 4
	wins = 0
	loss = 0
	#Busca velas inicia a quantidade de velas antes para dar certo a faixa de horário
	vls = iq_bot.iq_api.get_candles(par, 60*timeframe, velas+2, time.time())
	for idx, v in enumerate(vls):
		if idx== 0:
			if debug:
				print("")
				print("")
				print(stampToDate(int(v["at"]/1000000000),'%d/%m/%Y %H:%M:%S'),sep="", end="")
				print("")
				print("")
		elif idx > 0 and idx+1 < len(vls):
			if debug:
				print(c.rs, end="")
				print(stampToDate(int(v["from"]),'%H:%M'), sep="", end="")
				print(stampToDate(int(v["at"]/1000000000),'-%M'),sep="", end="")
			
			#Vela Atual é a Vela que fechou idx devo pegar o topo e base dessa...
			fechada = vls[idx]
			topo = fechada['max'] 
			base = fechada['min'] 
			#Topo e base velas atual fechada que é nossa referencia.
			if debug:
				print(" ", format(topo, casas), "▲ ", format(base, casas), "▼ ", sep="", end="")
			#Funcao sinal para melhorar assertividade.
			if S_passareto():
			#if S_fechoudentro(idx, vls):
			#if S_engolfo(idx, vls):
			#if S_desalinhamentodasgalaxias(idx, vls):
			#if S_alinhamentodasgalaxias(idx, vls):
				if debug:
					anterior = vls[idx-1]
					print("")
					print("# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #")
					
					print("Vela Anterior: ", stampToDate(int(anterior["from"]),'%M'), stampToDate(int(anterior["to"]),'-%M'),"	Topo:", anterior["max"], "▲ Base:",  anterior["min"], "▼ Close:", anterior["close"],".")


					print("   Vela Atual: ", stampToDate(int(fechada["from"]),'%M'), stampToDate(int(fechada["to"]),'-%M'),"	Topo:", fechada["max"], "▲ Base:",  fechada["min"], "▼ Close:", fechada["close"],".", end="")
				#Maxima e mínima da vela atual.
				#simula o monitoramento da proxima vela e verifica a estratégia e o resultado
				#busca velas por segundo nos 29 primeiros.
				segundos = timeframe*60-31
				vlssinal = iq_bot.iq_api.get_candles(par, 1, segundos+1, int(fechada["to"])+segundos)
				for idxs, vs in enumerate(vlssinal):
					if idxs>2:
						#if debug:
							#print(stampToDate(int(vs["at"]/1000000000),'%H:%M:%S'),sep="-", end=" ")
						# O preco for maior que o topo anterior ou menor que a base

						cursor = vs["close"]
						if cursor >= topo or cursor <= base:
							if debug:
								print("",stampToDate(int(vs["to"]),'%M:%S'), end="")
							# O preco for menor que a base CALL
							if cursor <= base:
								if debug:
									print(c.gr," ▲ ", sep="", end="")
									print(c.rs, format(cursor, casas), sep="", end="")						 
									velaentrada = vs
									print('')
									print("   Vela Entr.: ", stampToDate(int(velaentrada["from"]),'%M'), stampToDate(int(velaentrada["at"]/1000000000),'-%M:%S')," Topo:", velaentrada["max"], "▲ Base:",  velaentrada["min"], "▼ Close:", velaentrada["close"],".")   

									proxima = vls[idx+1]
									print("   Vela Prox.: ", stampToDate(int(proxima["from"]),'%M'), stampToDate(int(proxima["to"]),'-%M'),"	Topo:", proxima["max"], "▲ Base:",  proxima["min"], "▼ Close:", proxima["close"],".")
									print("# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #")
								if cursor < vls[idx+1]["close"]:
									wins += 1
								else:
									loss += 1
							# O preco for maior que o topo PUT
							if cursor >= topo:
								if debug:
									print(c.rd," ▼ ", sep="", end="")
									print(c.rs, format(cursor, casas), sep="", end="")
									velaentrada = vs
									print('')
									print("   Vela Entr.: ", stampToDate(int(velaentrada["from"]),'%M'), stampToDate(int(velaentrada["to"]),'-%M:%S')," Topo:", velaentrada["max"], "▲ Base:",  velaentrada["min"], "▼ Close:", velaentrada["close"],".")	   

									proxima = vls[idx+1]
									print("   Vela Prox.: ", stampToDate(int(proxima["from"]),'%M'), stampToDate(int(proxima["to"]),'-%M'),"	Topo:", proxima["max"], "▲ Base:",  proxima["min"], "▼ Close:", proxima["close"],".")										
									print("# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #")
								if cursor > vls[idx+1]["close"]:
									wins += 1
								else:
									loss += 1
							break
						elif idxs==segundos:
							if debug:
								print("	   ", end="")
								print("")
			else:
				if debug:
					print("	   ", end="")
					print("")
	return calculaAssertividade(wins, loss)
def catalogandofractal():
	global debug, casas
	if debug:
		print(c.rs)
		print(c.BYellow, "Catalogando ", par, "...", c.rs, sep="")
		print(c.rs)
		print("# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #")
		print("")
	#zera variáveis
	velas = 10
	wins = 0
	loss = 0
	#Busca velas inicia a quantidade de velas antes para dar certo a faixa de horário
	vls = iq_bot.iq_api.get_candles(par, 60*timeframe, velas+2, time.time())
	for idx, v in enumerate(vls):
		if idx== 0:
			if debug:
				print("")
				print("")
				print(stampToDate(int(v["at"]/1000000000),'%d/%m/%Y %H:%M:%S'),sep="", end="")
				print("")
				print("")
		elif idx > 0 and idx+1 < len(vls):
			if debug:
				print(c.rs, end="")
				print(stampToDate(int(v["from"]),'%H:%M'), sep="", end="")
				print(stampToDate(int(v["at"]/1000000000),'-%M'),sep="", end="")
			
			#Vela Atual é a Vela que fechou idx devo pegar o topo e base dessa...
			fechada = vls[idx]
			topo = fechada['max'] 
			base = fechada['min'] 
			#Topo e base velas atual fechada que é nossa referencia.
			if debug:
				print(" ", format(topo, casas), "▲ ", format(base, casas), "▼ ", sep="", end="")
			#Funcao sinal para melhorar assertividade.
			if S_passareto():
			#if S_fechoudentro(idx, vls):
			#if S_engolfo(idx, vls):
			#if S_desalinhamentodasgalaxias(idx, vls):
			#if S_alinhamentodasgalaxias(idx, vls):
				if debug:
					anterior = vls[idx-1]
					print("")
					print("# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #")
					
					print("Vela Anterior: ", stampToDate(int(anterior["from"]),'%M'), stampToDate(int(anterior["to"]),'-%M'),"	Topo:", anterior["max"], "▲ Base:",  anterior["min"], "▼ Close:", anterior["close"],".")


					print("   Vela Atual: ", stampToDate(int(fechada["from"]),'%M'), stampToDate(int(fechada["to"]),'-%M'),"	Topo:", fechada["max"], "▲ Base:",  fechada["min"], "▼ Close:", fechada["close"],".", end="")
				#Maxima e mínima da vela atual.
				#simula o monitoramento da proxima vela e verifica a estratégia e o resultado
				#busca velas por segundo nos 29 primeiros.
				segundos = 29
				vlssinal = iq_bot.iq_api.get_candles(par, 1, segundos+1, int(fechada["to"])+segundos)
				for idxs, vs in enumerate(vlssinal):
					if idxs>2:
						#if debug:
							#print(stampToDate(int(vs["at"]/1000000000),'%H:%M:%S'),sep="-", end=" ")
						# O preco for maior que o topo anterior ou menor que a base

						cursor = vs["close"]
						if cursor >= topo or cursor <= base:
							if debug:
								print("",stampToDate(int(vs["to"]),'%M:%S'), end="")
							# O preco for menor que a base CALL
							if cursor <= base:
								if debug:
									print(c.gr," ▲ ", sep="", end="")
									print(c.rs, format(cursor, casas), sep="", end="")						 
									velaentrada = vs
									print('')
									print("   Vela Entr.: ", stampToDate(int(velaentrada["from"]),'%M'), stampToDate(int(velaentrada["at"]/1000000000),'-%M:%S')," Topo:", velaentrada["max"], "▲ Base:",  velaentrada["min"], "▼ Close:", velaentrada["close"],".")   

									proxima = vls[idx+1]
									print("   Vela Prox.: ", stampToDate(int(proxima["from"]),'%M'), stampToDate(int(proxima["to"]),'-%M'),"	Topo:", proxima["max"], "▲ Base:",  proxima["min"], "▼ Close:", proxima["close"],".")
									print("# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #")
								if cursor < vls[idx+1]["close"]:
									wins += 1
								else:
									loss += 1
							# O preco for maior que o topo PUT
							if cursor >= topo:
								if debug:
									print(c.rd," ▼ ", sep="", end="")
									print(c.rs, format(cursor, casas), sep="", end="")
									velaentrada = vs
									print('')
									print("   Vela Entr.: ", stampToDate(int(velaentrada["from"]),'%M'), stampToDate(int(velaentrada["to"]),'-%M:%S')," Topo:", velaentrada["max"], "▲ Base:",  velaentrada["min"], "▼ Close:", velaentrada["close"],".")	   

									proxima = vls[idx+1]
									print("   Vela Prox.: ", stampToDate(int(proxima["from"]),'%M'), stampToDate(int(proxima["to"]),'-%M'),"	Topo:", proxima["max"], "▲ Base:",  proxima["min"], "▼ Close:", proxima["close"],".")										
									print("# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #")
								if cursor > vls[idx+1]["close"]:
									wins += 1
								else:
									loss += 1
							break
						elif idxs==segundos:
							if debug:
								print("	   ", end="")
								print("")
			else:
				if debug:
					print("	   ", end="")
					print("")
	return calculaAssertividade(wins, loss)
def parseCommandLine(args):

	desc = 'Horizon Bot para IQ Option.'
	parser = argparse.ArgumentParser(description=desc)

	hlp = 'SSID cookie da IQ Option.'
	parser.add_argument('--ssid', nargs='+', type=str, help=hlp)

	hlp = 'Usuário da IQ Option.'
	parser.add_argument('-u', '--user', nargs='+', type=str, help=hlp)

	hlp = 'Senha da IQ Option.'
	parser.add_argument('-p','--password', nargs='+', type=str, help=hlp)

	hlp = 'String contendo o par para negociação.'
	parser.add_argument('--par', nargs='+', type=str, help=hlp)

	hlp = 'Para negociação real.'
	parser.add_argument('--real', help=hlp, action="store_true")

	hlp = 'Tipo de negociação  binaria ou digital.'
	parser.add_argument('-o', '--option', nargs='+', type=str, help=hlp)

	hlp = 'Quanto porcento do valor da banca é usado para as entradas.'
	parser.add_argument('--percent', nargs='+', type=int, help=hlp)

	hlp = 'Valor da entrada, respeitando o tipo de moeda da conta.'
	parser.add_argument('--value', nargs='+', type=int, help=hlp)

	hlp = 'Meta de ganhos por sessão.'
	parser.add_argument('--meta', nargs='+', type=int, help=hlp)
	
	args = parser.parse_args()

	if args.ssid is None:
		parser.error('A opção -ssid precisa ser informada.')
		""""
		if args.user is None and args.password is not None:
			parser.error('A opção -u precisa ser informada junto com a senha.')

		if args.user is not None and args.password is None:
			parser.error('A opção -p precisa ser informada junto com usuário.')
		"""

	if args.par is None:
		parser.error('A opção -par precisa ser informada. Exemplo: ETHUSD, XRPUSD, EOSUSD.')

	if args.option is not None:
		
		if  args.option[0] != 'binary'  and args.option[0] != 'digital':
			parser.error('Selecione entre binary ou digital ou deixe em branco para usar o melhor payout.')

	if args.percent is not None:
		if  args.percent[0] > 50 or args.percent[0] < 1:
			parser.error('Informe um valor entre 1 e 50%.')
	
	if args.value is not None:
		if  args.value[0] < 1:
			parser.error('Informe um valor maior que 1.')
	
	return args   
def variaveislinhadecomando(parseCommandLine):
	global iq_bot
	args = parseCommandLine(sys.argv[1:])
	ssid = args.ssid[0]
	par = args.par[0].upper()
	balance = 'REAL' if args.real else 'PRACTICE'

	#digital = 1 binario = 2
	option = 2 if args.option is None else 1 if args.option[0] == 'digital' else 2 if args.option[0] == 'binary' else 0

	meta = 0 if args.meta is None else args.meta[0]

	porcentagem = 0 if args.percent is None else args.percent[0]
	entrada = 0 if args.value is None else args.value[0]

	return meta, option, par,balance,porcentagem,entrada,ssid
meta, option, par, balance, porcentagem, entrada, ssid = variaveislinhadecomando(parseCommandLine)

def parametrosfixos():
	stop_loss = 100000
	stop_gain = 100000
	stop_time = datetime.strptime("2042-06-30 23:59:00", '%Y-%m-%d %H:%M:%S')
	direction = ''
	payoutmin = 70

	return stop_loss,stop_gain,stop_time,direction,payoutmin
stop_loss, stop_gain, stop_time, direction, payoutmin = parametrosfixos()

registro = logging.getLogger('iqoption_api')
logging.basicConfig(level=logging.DEBUG,format=''+par+' %(asctime)s | %(message)s', datefmt='%H:%M:%S')
logging.getLogger('iqoption_api').setLevel(logging.DEBUG)

iq_bot=IQ_BOT('','',ssid)

if iq_bot.conectar():
	teste = False
	#iq_bot.iq_api.inscrever_obter_velas(par, 1, ticker)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
timeframe = 1

sorosGale = 0
sorosGalefator = 1.1
sorosGaleLimite = 10

soros = 0
sorosFator = 0.1

limiteDeLoss = 3
WinsParaRetorno = 2
assertividadeMinima = 60

debug = True
debug = False


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
point = 0
pointAtual = 0
pointSinal = 0
porcento = 0
topo = 0
base = 0
Vmax = 0
Vmin = 0
entradas = 0
entrar = False
openoption = False

segundosAntesdaExpiracao = 30
if option==2 and timeframe>=15: #digital = 1 binario = 2
	segundosAntesdaExpiracao = 300




def on_message(ws, message):
	global pointSinal, entrar
	if message!="Connected":
		price = json.loads(message)	
		pointSinal = price['bid']
		if entrar:
			diff = abs(pointAtual-pointSinal)*100000
			if diff >= 5:
				if pointAtual>pointSinal:
					if openoption:
						compra(par, iq_bot.vRentrada, 'put', timeframe, pointAtual)
				else:
					if openoption:
						compra(par, iq_bot.vRentrada, 'call', timeframe, pointAtual)
				entrar = False
			if diff >= 2:
				if pointAtual>pointSinal:
					print("→", now('%H:%M:%S')," ", par," ", c.rd, "▼", c.rs, round(diff, 2), " - ", round(pointAtual, 6), sep="")
				else:
					print("→", now('%H:%M:%S')," ", par," ", c.gr, "▲", c.rs, round(diff, 2), " - ", round(pointAtual, 6), sep="")

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    ws.send("{\"userKey\":\"wsylpS9_5cP5kt3NUfVg\", \"symbol\":\""+par+"\"}")

ws = websocket.WebSocketApp("wss://marketdata.tradermade.com/feedadv", on_open = on_open, on_message = on_message, on_error = on_error, on_close = on_close)
threading.Thread(target=ws.run_forever, daemon=True).start()


registro.info('Iniciando...')



def ticker(vela):
	global entrar, point, pointAtual, porcento, topo, base, openoption, par, timeframe, Vmax, Vmin,entradas,iq_bot
	
	pointAtual = vela['close']
	if entrar:
		pass
try:
	# entra no loop de ordens... 
	while True:
		# Começa o processamento verifica o stop time e o payout a cada ciclo antes de entrar
		stoptime(stop_time)
		stopgain(iq_bot.lucro, stop_gain)
		stoploss(iq_bot.lucro, stop_loss)
		while True:
			minutos = float(((datetime.now() + timedelta(seconds=1)).strftime('%M.%S'))) + (timeframe)
			if ((minutos % (timeframe)) == 0):
				break
			time.sleep(1)
		registro.info('Reiniciando...')

		if openoption: #Se o par estiver aberto
			openoption = allopen(iq_bot.option)[par]
			if not openoption: #Se fechou agora para de buscar velas
				iq_bot.iq_api.desinscrever_obter_velas(par, 1)				
		else:
			iq_bot.emAnalize = False
			openoption = allopen(iq_bot.option)[par]
			if openoption: #Se abriu agora busca assertividade
				iq_bot.iq_api.inscrever_obter_velas(par, 1, ticker)

		if openoption:
			registro.info('{} ({}) [${}] {}'.format(iq_bot.iq_api.perfil['first_name'], iq_bot.iq_api.perfil['email'], real_br_money_mask(iq_bot.iq_api.valor_do_saldo(iq_bot.tipo_id)).rjust(11," "), iq_bot.iq_api.tipo_saldo(iq_bot.tipo_id).upper()))
			#busca o valor máximo
			exposure = iq_bot.iq_api.get_active_exposure(par, timeframe, iq_bot.option)
			maxcall = exposure["call"]
			maxput = exposure["put"]
		else:
			registro.info('Aguardando abertura. {} ({}) | ${} |'.format(iq_bot.iq_api.perfil['first_name'], iq_bot.iq_api.perfil['email'], real_br_money_mask(iq_bot.iq_api.valor_do_saldo(iq_bot.tipo_id)).rjust(11," "), iq_bot.iq_api.tipo_saldo(iq_bot.tipo_id).upper()))
			maxcall = 10000
			maxput = 10000
		
		# Sincroniza entrada entre 3 segundos e 30
		
		sincronizaSegundos(20, 30)
	
		registro.info('Pega parametros.')
		if openoption:
			entrar = True
		registro.info('Entra.')

		espera = (timeframe*60)-int(now('%S'))-segundosAntesdaExpiracao
		registro.info('Espera {} segundos.'.format(espera))

		if espera>0:
			time.sleep(espera)
		registro.info('Para até reiniciar.')
		entrar = False
				#Entra 10 segundos antes.




except KeyboardInterrupt:
	registro.info('Obrigado!!!')
	sys.exit()
