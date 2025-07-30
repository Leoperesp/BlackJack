from flask import Flask, render_template, request, session, redirect, url_for
import random

app = Flask(__name__)
app.secret_key = 'blackjack_secret_key'

SUITS = ['Corazón', 'Diamante', 'Trébol', 'Pica']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
VALUES = {'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10}


def create_deck():
    return [(rank, suit) for suit in SUITS for rank in RANKS]

def shuffle_deck(deck):
    random.shuffle(deck)
    return deck

def hand_value(hand):
    value = sum(VALUES[card[0]] for card in hand)
    aces = sum(1 for card in hand if card[0] == 'A')
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

def deal_card(deck):
    return deck.pop()

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/start')
def start():
    deck = shuffle_deck(create_deck())
    session['deck'] = deck
    session['player_hand'] = [deal_card(deck), deal_card(deck)]
    session['pc_hand'] = [deal_card(deck), deal_card(deck)]
    session['round'] = 1
    session['player_score'] = 0
    session['pc_score'] = 0
    session['history'] = []
    return redirect(url_for('game'))

@app.route('/game')
def game():
    pc_reveal = session.get('pc_reveal', False)
    pc_animating = session.get('pc_animating', False)
    last_winner = session.pop('last_winner', None)
    if pc_reveal:
        pc_hand = session['pc_hand']
    else:
        pc_hand = [session['pc_hand'][0], ('?', '?')]
    return render_template('game.html',
        player_hand=session['player_hand'],
        pc_hand=pc_hand,
        round=session['round'],
        player_score=session['player_score'],
        pc_score=session['pc_score'],
        history=session['history'],
        pc_animating=pc_animating,
        last_winner=last_winner)

@app.route('/hit')
def hit():
    deck = session['deck']
    player_hand = session['player_hand']
    player_hand.append(deal_card(deck))
    session['deck'] = deck
    session['player_hand'] = player_hand
    if hand_value(player_hand) > 21:
        return redirect(url_for('stand'))
    return redirect(url_for('game'))

@app.route('/stand')
def stand():
    session['pc_reveal'] = True
    session['pc_animating'] = True
    return redirect(url_for('pc_turn'))


# Nueva ruta para animar el turno del PC
@app.route('/pc_turn')
def pc_turn():
    deck = session['deck']
    pc_hand = session['pc_hand']
    # Si el PC debe pedir carta, la pide y vuelve a mostrar la página
    if hand_value(pc_hand) < 17:
        pc_hand.append(deal_card(deck))
        session['pc_hand'] = pc_hand
        session['deck'] = deck
        session['pc_reveal'] = True
        session['pc_animating'] = True
        return redirect(url_for('game'))
    # Si ya no pide más, calcular resultado
    session['pc_hand'] = pc_hand
    player_val = hand_value(session['player_hand'])
    pc_val = hand_value(pc_hand)
    if player_val > 21:
        winner = 'PC'
    elif pc_val > 21 or player_val > pc_val:
        winner = 'Jugador'
    elif player_val < pc_val:
        winner = 'PC'
    else:
        winner = 'Empate'
    session['history'].append({
        'round': session['round'],
        'player': player_val,
        'pc': pc_val,
        'winner': winner,
        'player_hand': list(session['player_hand']),
        'pc_hand': list(pc_hand)
    })
    if winner == 'Jugador':
        session['player_score'] += 1
    elif winner == 'PC':
        session['pc_score'] += 1
    session['last_winner'] = winner
    session['pc_animating'] = False

    # Terminar si alguien llega a 2 victorias
    if session['player_score'] == 2 or session['pc_score'] == 2 or session['round'] >= 3:
        return redirect(url_for('result'))

    # Siguiente ronda
    deck = shuffle_deck(deck)
    session['deck'] = deck
    session['player_hand'] = [deal_card(deck), deal_card(deck)]
    session['pc_hand'] = [deal_card(deck), deal_card(deck)]
    session['round'] += 1
    session['pc_reveal'] = False
    return redirect(url_for('game'))

@app.route('/result')
def result():
    if session['player_score'] > session['pc_score']:
        final_winner = '¡Ganaste la serie!'
    elif session['player_score'] < session['pc_score']:
        final_winner = 'El PC gana la serie.'
    else:
        final_winner = 'Empate en la serie.'
    return render_template('result.html',
        history=session['history'],
        player_score=session['player_score'],
        pc_score=session['pc_score'],
        final_winner=final_winner)

if __name__ == '__main__':
    app.run(debug=True)
