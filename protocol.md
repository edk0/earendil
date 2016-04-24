# Earendil IRC Protocol Specification

*Version 0.0*

This document compiles the information in [RFC 2812][] in a
straightforward way, along with a tool to extract this information
into a JSON format suitable for generating code.

The messages in this document are divided into sections, corresponding
to sections of the RFC.

  [RFC 2812]: https://tools.ietf.org/html/rfc2812

[TOC]

## How to Read This Document

`<angle brackets>` denote a required argument.

`[square brackets]` denote an optional argument, that fills in from the left first.

`(round brackets)` denote an optional argument that fills in from the right first.

`<a trailing comma,>` indicates a comma-seperated list.

`<a trailing underscore_>` indicates a space-seperated list.

`<int:a prepended type>` indicates a special type.

`<flag(str):types>` are true if present, and false if absent. When present, the value is expected to be `str` (but not required to be, generally).

Literal text is also mostly ignored, but useful for context.

## 3.1 Connection Registration

([in the RFC](https://tools.ietf.org/html/rfc2812#section-3.1))

### PASS <password> {#pass}

Related: 461, 462.

### NICK <nickname> {#nick}

Related: 431, 432, 433, 436, 437, 484.

### USER <user> <int:mode> * <realname> {#user}

Related: 461, 462.

### OPER <name> <password> {#oper}

Related: 461, 381, 491, 464.

### MODE <name> <mode> {#mode}

Related: 461, 467, 477, 482, 441, 472, 502, 501, 324, 367, 368, 348, 349, 346, 347, 325, 221.

FIXME multiples.

### SERVICE <nickname> * <distribution> <int:type> 0 <info> {#service}

Related: 462, 461, 432, 383, 002, 004.

### QUIT [message] {#quit}

### SQUIT <server> <comment> {#s-quit}

Related: 481, 402, 461.

## 3.2 Channel Operations

([in the RFC](https://tools.ietf.org/html/rfc2812#section-3.2))

### JOIN <channels,> [keys,] {#channel-join}

Related: 461, 474, 473, 475, 471, 476, 403, 405, 407, 437, 332.

### PART <channels,> [message] {#channel-part}

Related: 461, 403, 442.

### TOPIC <channel> [topic] {#topic}

Related: 461, 442, 331, 332, 482, 477.

### NAMES [channels,] [target] {#names}

Related: 402, 353, 366.

### LIST [channels,] [target] {#list}

Related: 402, 322, 323.

### INVITE <nickname> <channel> {#invite}

Related: 461, 401, 442, 443, 482, 341, 301.

### KICK <channels,> <users,> [comment] {#kick}

Related: 461, 403, 476, 482, 441, 442.

## 3.3 Sending Messages

([in the RFC](https://tools.ietf.org/html/rfc2812#section-3.3))

### PRIVMSG <target> <message> {#privmsg}

Related: 411, 412, 404, 413, 414, 407, 401, 301.

### NOTICE <target> <message> {#notice}

Related: 411, 412, 404, 413, 414, 407, 401, 301.

## 3.4 MOTD Message

([in the RFC](https://tools.ietf.org/html/rfc2812#section-3.4))

### MOTD [target] {#motd}

Related: 375, 372, 376, 422.

### LUSERS [mask] [target] {#lusers}

Related: 251, 252, 253, 254, 255, 402.

### VERSION [target] {#version}

Related: 402, 351.

### STATS [query] [target] {#stats}

Related: 402, 211, 242, 212, 243, 219.

### LINKS (server) (mask) {#links}

Related: 402, 364, 365.

### TIME [target] {#time}

Related: 402, 391.

### CONNECT <target> <int:port> [remote] {#server-connect}

Related: 402, 481, 461.

### TRACE [target] {#trace}

Related: 402, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 261, 262.

### ADMIN [target] {#admin}

Related: 402, 256, 257, 258, 259.

### INFO [target] {#info}

Related: 402, 371, 374.

## 3.5 Service Query and Commands

([in the RFC](https://tools.ietf.org/html/rfc2812#section-3.5))

### SERVLIST [mask] [type] {#serv-list}

Related: 234, 235.

### SQUERY <servicename> <text> {#s-query}

Related: 411, 412, 404, 413, 414, 407, 401, 301.

## 3.6 User Based Queries

([in the RFC](https://tools.ietf.org/html/rfc2812#section-3.6))

### WHO [mask] [flag(o):operators] {#who}

Related: 402, 352, 315.

### WHOIS [target] <masks,> {#who-is}

Related: 402, 431, 311, 319, 312, 301, 313, 317, 401, 318.

### WHOWAS <nicknames,> [int:count] [target] {#who-was}

Related: 431, 406, 314, 312, 369.

## 3.7 Miscellaneous Messages

([in the RFC](https://tools.ietf.org/html/rfc2812#section-3.7))

### KILL <nickname> <comment> {#kill}

Related: 481, 461, 401, 483.

### PING <server1> [server2] {#ping}

Related: 409, 402.

### PONG <server> [server2] {#pong}

Related: 409, 402.

### ERROR <message> {#error}

## 4 Optional Features

([in the RFC](https://tools.ietf.org/html/rfc2812#section-4))

### AWAY [text] {#away}

Related: 305, 306.

### REHASH {#rehash}

Related: 382, 481.

### DIE {#die}

Related: 481.

### RESTART {#restart}

Related: 481.

### SUMMON <user> [target] [channel] {#summon}

Related: 411, 424, 444, 402, 445, 342.

### USERS [target] {#users}

Related: 402, 424, 392, 393, 395, 394, 446.

### WALLOPS <message> {#wall-ops}

Related: 461.

### USERHOST <nickname> {#user-host}

Related: 302, 461.

FIXME many nicknames.

### ISON <nickname> {#is-on}

Related: 303, 461.

FIXME many nicknames.

## 5.1 Command Responses

([in the RFC](https://tools.ietf.org/html/rfc2812#section-5.1))

### 001 <target> <message> {#welcome}

### 002 <target> <message> {#your-host}

### 003 <target> <message> {#created}

### 004 <target> <message> {#my-info}

### 005 <target> <message> {#bounce}

### 200 <target> Link <version> <destination> <next> <protocol-version> <link-uptime> <back-send-q> <up-send-q> {#trace-link-reply}

### 201 <target> Try. <class> <server> {#trace-connecting}

### 202 <target> H.S. <class> <server> {#trace-handshake}

### 203 <target> ???? <class> [ip] {#trace-unknown}

### 204 <target> Oper <class> <nickname> {#trace-operator}

### 205 <target> User <class> <nickname> {#trace-user}

### 206 <target> Serv <class> <s> <c> <server> <hostmask> <protocol-version> {#trace-server}

### 207 <target> Service <class> <name> <type> <active-type> {#trace-service}

### 208 <target> <newtype> 0 <name> {#trace-newtype}

### 209 <target> Class <class> <int:count> {#trace-class}

### 211 <target> <name> <sendq> <int:sent-messages> <int:sent-kbytes> <int:recv-messages> <int:recv-kbytes> <int:uptime> {#stats-link-info}

### 212 <target> <command> <int:count> <int:bytes> <int:remote-count> {#stats-commands}

### 219 <target> <letter> :End of STATS report {#stats-end}

### 221 <target> <mode> {#user-mode-is}

### 234 <target> <name> <server> <mask> <type> <int:hopcount> <info> {#serv-list-reply}

### 235 <target> <mask> <type> :End of service listing {#serv-list-end}

### 242 <target> <message> {#stats-uptime}

### 243 <target> O <hostmask> * <name> {#stats-oline}

### 251 <target> <message> {#luser-client}

### 252 <target> <int:count> :operator(s) online {#luser-op}

### 253 <target> <int:count> :unknown connection(s) {#luser-unknown}

### 254 <target> <int:count> :channels formed {#luser-channels}

### 255 <target> <message> {#luser-me}

### 256 <target> <server> :Administrative info {#admin-me}

### 257 <target> <message> {#admin-loc1}

### 258 <target> <message> {#admin-loc2}

### 259 <target> <email> {#admin-email}

### 261 <target> File <logfile> <debug-level> {#trace-log}

### 262 <target> <server> <version> :End of TRACE {#trace-end}

### 263 <target> <command> :Please wait a while and try again. {#try-again}

### 301 <target> <nickname> <message> {#away-reply}

### 302 <target> <message> {#user-host-reply}
FIXME parse data!

### 303 <target> <message> {#is-on-reply}
FIXME parse data!

### 305 <target> :You are no longer marked as being away {#unaway-reply}

### 306 <target> :You have been marked as being away {#now-away-reply}

### 311 <target> <nickname> <user> <host> * <realname> {#who-is-user}

### 312 <target> <nickname> <server> <info> {#who-is-server}

### 313 <target> <nickname> :is an IRC operator {#who-is-operator}

### 314 <target> <nickname> <user> <host> * <realname> {#who-was-user}

### 315 <target> <name> :End of WHO list {#who-end}

### 317 <target> <nickname> <int:time> :seconds idle {#who-is-idle}

### 318 <target> <nickname> :End of WHOIS list {#who-is-end}

### 319 <target> <nickname> <channels> {#who-is-channels}

### 322 <target> <channel> <int:visible> <topic> {#list-reply}

### 323 <target> :End of LIST {#list-end}

### 324 <target> <channel> <mode> <params> {#channel-mode-is}

### 325 <target> <channel> <nickname> {#uniq-op-is}

### 331 <target> <channel> :No topic is set {#no-topic-reply}

### 332 <target> <channel> <topic> {#topic-reply}

### 341 <target> <channel> <nick> {#inviting}

### 342 <target> <user> :Summoning user to IRC {#summoning}

### 346 <target> <channel> <mask> {#invite-list}

### 347 <target> <channel> :End of channel invite list {#invite-list-end}

### 348 <target> <channel> <mask> {#except-list}

### 349 <target> <channel> :End of channel exception list {#except-list-end}

### 351 <target> <version> <server> <comments> {#version-reply}

### 352 <target> <channel> <user> <host> <server> <nickname> <props> <realname> {#who-reply}

### 353 <target> <mode> <channel> <nicknames_> {#names-reply}

### 364 <target> <mask> <server> <info> {#links-reply}

### 365 <target> <mask> :End of LINKS list {#links-end}

### 366 <target> <channel> :End of NAMES list {#names-end}

### 367 <target> <channel> <mask> {#ban-list}

### 368 <target> <channel> :End of channel ban list {#ban-list-end}

### 369 <target> <nickname> :End of WHOWAS {#who-was-end}

### 371 <target> <info> {#info-reply}

### 372 <target> <message> {#motd-text}

### 374 <target> :End of INFO list {#info-end}

### 375 <target> <message> {#motd-start}

### 376 <target> :End of MOTD command {#motd-end}

### 381 <target> :You are now an IRC operator {#youre-oper}

### 382 <target> <file> Rehashing {#rehashing}

### 383 <target> <message> {#youre-service}

### 391 <target> <server> <time> {#time-reply}

### 392 <target> :UserID   Terminal  Host {#users-start}

### 393 <target> <message> {#users-reply}

### 394 <target> :End of users {#users-end}

### 395 <target> :Nobody logged in {#no-users}

## 5.2 Error Replies

([in the RFC](https://tools.ietf.org/html/rfc2812#section-5.2))

### 401 <target> <nickname> :No such nick/channel {#no-such-nick}

### 402 <target> <server> :No such server {#no-such-server}

### 403 <target> <channel> :No such channel {#no-such-channel}

### 404 <target> <channel> :Cannot send to channel {#cant-send-to-chan}

### 405 <target> <channel> :You have joined too many channels {#too-many-channels}

### 406 <target> <nickname> :There was no such nickname {#was-no-such-nick}

### 407 <target> <orig-target> <message> {#too-many-targets}

### 408 <target> <name> :No such service {#no-such-service}

### 409 <target> :No origin specified {#no-origin}

### 411 <target> :No recipient given {#no-recipient}

### 412 <target> :No text to send {#no-text-to-send}

### 413 <target> <mask> :No toplevel domain specified {#no-top-level}

### 414 <target> <mask> :Wildcard in toplevel domain {#wild-top-level}

### 415 <target> <mask> :Bad Server/host mask {#bad-mask}

### 421 <target> <command> :Unknown command {#unknown-command}

### 422 <target> :MOTD File is missing {#no-motd}

### 423 <target> <server> :No administrative info available {#no-admin-info}

### 424 <target> <message> {#file-error}

### 431 <target> :No nickname given {#no-nickname-given}

### 432 <target> <nickname> :Erroneous nickname {#erroneus-nickname}

### 433 <target> <nickname> :Nickname is already in use {#nickname-in-use}

### 436 <target> <nickname> <message> {#nick-collision}

### 437 <target> <name> :Nick/channel is temporarily unavailable {#unavail-resource}

### 441 <target> <nickname> <channel> :They aren't on that channel {#user-not-in-channel}

### 442 <target> <channel> :You're not on that channel {#not-on-channel}

### 443 <target> <user> <channel> :is already on channel {#user-on-channel}

### 444 <target> <user> :User not logged in {#no-login}

### 445 <target> :SUMMON has been disabled {#summon-disabled}

### 446 <target> :USERS has been disabled {#users-disabled}

### 451 <target> :You have not registered {#not-registered}

### 461 <target> <command> :Not enough parameters {#need-more-params}

### 462 <target> :Unauthorized command (already registered) {#already-registered}

### 463 <target> :Your host isn't among the privileged {#no-perm-for-host}

### 464 <target> :Password incorrect {#password-mismatch}

### 465 <target> :You are banned from this server {#youre-banned-creep}

### 466 <target> {#you-will-be-banned}

### 467 <target> <channel> :Channel key already set {#key-set}

### 471 <target> <channel> :Cannot join channel (+l) {#channel-is-full}

### 472 <target> <char> :is unknown mode char to me {#unknown-mode}

### 473 <target> <channel> :Cannot join channel (+i) {#invite-only-chan}

### 474 <target> <channel> :Cannot join channel (+b) {#banned-from-chan}

### 475 <target> <channel> :Cannot join channel (+k) {#bad-channel-key}

### 476 <target> <channel> :Bad Channel Mask {#bad-chan-mask}

### 477 <target> <channel> :Channel doesn't support modes {#no-chan-modes}

### 478 <target> <channel> <char> :Channel list is full {#ban-list-full}

### 481 <target> :Permission Denied- You're not an IRC operator {#no-privileges}

### 482 <target> <channel> :You're not channel operator {#chan-op-privs-needed}

### 483 <target> :You can't kill a server! {#cant-kill-server}

### 484 <target> :Your connection is restricted! {#restricted}

### 485 <target> :You're not the original channel operator {#uniq-op-privs-needed}

### 491 <target> :No O-lines for your host {#no-oper-host}

### 501 <target> :Unknown MODE flag {#user-mode-unknown-flag}

### 502 <target> :Cannot change mode for other users {#users-dont-match}

## CTCP

# Conclusion
