#!/usr/bin/python
# -*- coding: utf-8 -*-

# Defs
#
# Marcelo H. Terres <mhterres@gmail.com>
# 2014-06-02
#
# Versao 0.2.1.1

import socket
import time
import re
import psycopg2
import psycopg2.extras
import ConfigParser

from astdemo_classes import Config
from astdemo_classes import connectAMI
from astdemo_classes import activeLogs
from astdemo_classes import ManagerDict
from astdemo_classes import ManagerDictEvents

def sipPeer(sip):

	activeLogs('/tmp','astdemo_defs','err')

	myConnect=connectAMI()
	s = myConnect.socket

	s.send('Action: SIPshowpeer\nPeer: ' + sip + '\n\n')
	time.sleep (0.1)

	data = s.recv(65536)

	mgrdict=ManagerDict(data)

	returnmsg = "Extension %s informations: " % sip
	returnmsg += "\r"

	if data.find("Peer " + sip + " not found") > 0:

		returnmsg += "Ramal " + sip + " não registrado.\n"
	else:		
		returnmsg += "CallerID: " + mgrdict.getitem('Callerid') 
		returnmsg += "IP: " + mgrdict.getitem('Address-IP')
		returnmsg += "Codecs: " + mgrdict.getitem('Codecs')
		returnmsg += "Status: " + mgrdict.getitem('Status')
		returnmsg += "User Agent: " + mgrdict.getitem('SIP-Useragent')

	s.close()

	return returnmsg

def infoVoIP():

	activeLogs('/tmp','astdemo_defs','err')

	myConnect=connectAMI()
	s = myConnect.socket

	s.send('Action: CoreSettings\n\n')
	time.sleep (0.1)

	data = s.recv(65536)

	mgrdict=ManagerDict(data)

	returnmsg = "VoIP Informations"
	returnmsg += "\r"
	returnmsg += "Asterisk Version %s " % mgrdict.getitem('AsteriskVersion') 

	s.send('Action: CoreStatus\n\n')
	time.sleep (0.1)

	data = s.recv(65536)

	mgrdict=ManagerDict(data)

	returnmsg += "Started: " + mgrdict.getitem('CoreStartupDate').replace('\r','') + ' - ' + mgrdict.getitem('CoreStartupTime')
	returnmsg += "Last reload: " + mgrdict.getitem('CoreReloadDate').replace('\r','')  + ' - ' + mgrdict.getitem('CoreReloadTime')

	s.close()
	
	return returnmsg

def iaxPeers():

	myConnect=connectAMI()
	s = myConnect.socket

	s.send('Action: IAXpeers\n\n')
	time.sleep (0.1)

	data = s.recv(65535)

	mgrdictev=ManagerDictEvents(data,'PeerEntry')

	if not mgrdictev.isvalid:

		returnmsg = "IAX peers not found."
		return returnmsg
	
	else:

		returnmsg = "IAX peers Informations - %s peers found.\r" % str(mgrdictev.items) 

		for event in mgrdictev.events:


			returnmsg+="Peer: " + event['ObjectName'] 
			returnmsg+="Type: " + event['ChanObjectType'] 
			returnmsg+="IP: " + event['IPaddress'] 
			returnmsg+="Port: " + event['IPport'] 
			returnmsg+="Trunk: " + event['Trunk'] 
			returnmsg+="Status: " + event['Status'] 
			returnmsg += '\r'

	s.close()
	
	return returnmsg

def sipPeers():

	myConnect=connectAMI()
	s = myConnect.socket

	s.send('Action: SIPpeers\n\n')
	time.sleep (0.1)

	data = s.recv(65535)

	mgrdictev=ManagerDictEvents(data,'PeerEntry')

	if not mgrdictev.isvalid:

		returnmsg = "SIP peers not found."
		return returnmsg
	
	else:

		returnmsg = "SIP peers Informations - %s peers found.\r " % str(mgrdictev.items) 

		for event in mgrdictev.events:


			returnmsg+="Peer: " + event['ObjectName'] 
			returnmsg+="Type: " + event['ChanObjectType'] 
			returnmsg+="IP: " + event['IPaddress'] 
			returnmsg+="Port: " + event['IPport'] 
			returnmsg+="Video support: " + event['VideoSupport'] 
			returnmsg+="Realtime: " + event['RealtimeDevice'] 
			returnmsg+="Status: " + event['Status'] 
			returnmsg += '\r'

	s.close()
	
	return returnmsg

def getAsteriskRealtimeInformation(jid):

	cfg = Config()

	dsn = 'dbname=%s host=%s user=%s password=%s' % (cfg.asterisk_db_name, cfg.asterisk_db_host, cfg.asterisk_db_user, cfg.asterisk_db_pwd)

	conn = psycopg2.connect(dsn)
	curs = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	sql = "SELECT name,callerid,%s from %s where %s='%s';" % (cfg.asterisk_jid_field,cfg.asterisk_sip_table,cfg.asterisk_jid_field,jid)
	curs.execute(sql,)

	if not curs.rowcount:
		return ["","",""]

	row=curs.fetchone()
	name = row['name']
	callerid = row['callerid']
	return [name,jid,callerid]

def getJidExtension(extension):

	cfg = Config()

	dsn = 'dbname=%s host=%s user=%s password=%s' % (cfg.asterisk_db_name, cfg.asterisk_db_host, cfg.asterisk_db_user, cfg.asterisk_db_pwd)

	conn = psycopg2.connect(dsn)
	curs = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

	sql = "SELECT name,callerid,%s from %s where name='%s';" % (cfg.asterisk_jid_field,cfg.asterisk_sip_table,extension)
	curs.execute(sql,)

	if not curs.rowcount:
		return ""

	row=curs.fetchone()
	jid = row['jid']

	return jid

def showHelp():

  cfg = Config()

  returnmsg = "\r";
  returnmsg += "HELP\r";
  returnmsg += "Valid commands:\r";
  returnmsg += "\tcall <number> - make a call to <number> and play tt-monkeys.\r";

  if cfg.asterisk_realtime=="1":

    returnmsg += "\tcallerid - enable/Disable the callerid xmpp message on received calls.\r";
  else:

    returnmsg += "\tcallerid <extension> <jid> - enable/Disable the callerid xmpp message on received calls.\r";

  if cfg.asterisk_realtime=="1":

    returnmsg += "\tdnd <on|off|status> - enable/Disable or show Do Not Disturb status.\r";

  returnmsg += "\tinfo <voip|xmpp> - show VoIP or XMPP server informations.\r";
  returnmsg += "\thelp - show this help.\r";
  returnmsg += "\tiaxpeers - show IAX peers.\r";

  if cfg.asterisk_realtime=="1":

    returnmsg += "\tqueue <queue> - show <queue> members and statistics.\r";
    returnmsg += "\tqueuemsg <queue> <message> - send <message> to all members of queue <queue>.\r"
    returnmsg += "\tqueueon <queue> - join <queue>.\r"
    returnmsg += "\tqueueoff <queue> - leave <queue>.\r";

  returnmsg += "\tsippeer <extension> - show SIP informations of <extension>.\r";
  returnmsg += "\tsippeers - show SIP peers.\r";
  returnmsg += "\tversion - show astdemo version.\r";

  if cfg.asterisk_realtime=="1":

    returnmsg +="\twhoami - show basic informations about myself.\r";

  return returnmsg

def getSocketData(sck,cmd):

  sck.send(cmd + "\n")
  time.sleep (0.1)
  data = s.recv(65536)

  return data

def validNumber(jid,number):

  cfg = Config()

  dsn = 'dbname=%s host=%s user=%s password=%s' % (cfg.db_dbname, cfg.db_host, cfg.db_user, cfg.db_pwd)

  conn = psycopg2.connect(dsn)
  curs = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  sql = 'SELECT r.id FROM jids_phones as r,jids as j,phones as p where r.jid_id = j.id and r.phone_id=p.id and j.jid = %s and p.phone = %s'
  curs.execute(sql, (jid,number))

  if not curs.rowcount:
    return False

  return True

def getChannel(jid,number):

  cfg = Config()

  dsn = 'dbname=%s host=%s user=%s password=%s' % (cfg.db_dbname, cfg.db_host, cfg.db_user, cfg.db_pwd)

  conn = psycopg2.connect(dsn)
  curs = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  sql = 'SELECT p.channel FROM jids_phones as r,jids as j,phones as p where r.jid_id = j.id and r.phone_id=p.id and j.jid = %s and p.phone = %s'
  curs.execute(sql, (jid,number))

  if not curs.rowcount:
    return ""

  value = curs.fetchone()['channel']
  return value


