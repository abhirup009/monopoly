-- Monopoly Game Engine Database Schema
-- Version: 1.0.0

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===================
-- GAMES TABLE
-- ===================
CREATE TABLE games (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
    current_player_index INTEGER NOT NULL DEFAULT 0,
    turn_number INTEGER NOT NULL DEFAULT 0,
    turn_phase VARCHAR(30) NOT NULL DEFAULT 'pre_roll',
    doubles_count INTEGER NOT NULL DEFAULT 0,
    last_dice_roll INTEGER[] DEFAULT NULL,
    winner_id UUID DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Status values: waiting, in_progress, completed
-- Turn Phase values: pre_roll, awaiting_roll, awaiting_buy_decision,
--                    awaiting_jail_decision, post_roll

COMMENT ON TABLE games IS 'Main game state table';
COMMENT ON COLUMN games.status IS 'waiting, in_progress, completed';
COMMENT ON COLUMN games.turn_phase IS 'Current phase within a turn';
COMMENT ON COLUMN games.doubles_count IS 'Consecutive doubles rolled this turn';
COMMENT ON COLUMN games.last_dice_roll IS 'Array of [die1, die2] from last roll';

-- ===================
-- PLAYERS TABLE
-- ===================
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    model VARCHAR(50) NOT NULL,
    personality VARCHAR(50) NOT NULL,
    player_order INTEGER NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    cash INTEGER NOT NULL DEFAULT 1500,
    in_jail BOOLEAN NOT NULL DEFAULT FALSE,
    jail_turns INTEGER NOT NULL DEFAULT 0,
    get_out_of_jail_cards INTEGER NOT NULL DEFAULT 0,
    is_bankrupt BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_players_game_id ON players(game_id);
CREATE INDEX idx_players_game_order ON players(game_id, player_order);

COMMENT ON TABLE players IS 'Player state within a game';
COMMENT ON COLUMN players.model IS 'AI model: gpt-4, claude-3, llama-3, etc.';
COMMENT ON COLUMN players.personality IS 'Agent personality: aggressive, analytical, chaotic';
COMMENT ON COLUMN players.player_order IS 'Turn order (0, 1, 2)';
COMMENT ON COLUMN players.position IS 'Board position (0-39)';
COMMENT ON COLUMN players.jail_turns IS 'Number of turns spent in jail';

-- ===================
-- PROPERTY STATES TABLE
-- ===================
CREATE TABLE property_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    property_id VARCHAR(50) NOT NULL,
    owner_id UUID REFERENCES players(id) ON DELETE SET NULL,
    houses INTEGER NOT NULL DEFAULT 0,
    UNIQUE(game_id, property_id)
);

CREATE INDEX idx_property_states_game_id ON property_states(game_id);
CREATE INDEX idx_property_states_owner_id ON property_states(owner_id);

COMMENT ON TABLE property_states IS 'Runtime state of properties in a game';
COMMENT ON COLUMN property_states.property_id IS 'References static property data (e.g., boardwalk, park_place)';
COMMENT ON COLUMN property_states.houses IS '0-4 for houses, 5 for hotel';

-- ===================
-- CARD DECKS TABLE
-- ===================
CREATE TABLE card_decks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    deck_type VARCHAR(20) NOT NULL,
    card_order INTEGER[] NOT NULL,
    current_index INTEGER NOT NULL DEFAULT 0,
    UNIQUE(game_id, deck_type)
);

CREATE INDEX idx_card_decks_game_id ON card_decks(game_id);

COMMENT ON TABLE card_decks IS 'Shuffled card decks for each game';
COMMENT ON COLUMN card_decks.deck_type IS 'chance or community_chest';
COMMENT ON COLUMN card_decks.card_order IS 'Shuffled array of card indices';
COMMENT ON COLUMN card_decks.current_index IS 'Next card to draw';

-- ===================
-- GAME EVENTS TABLE (Action Log)
-- ===================
CREATE TABLE game_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_id UUID REFERENCES players(id) ON DELETE SET NULL,
    turn_number INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_game_events_game_id ON game_events(game_id);
CREATE INDEX idx_game_events_created_at ON game_events(created_at);
CREATE INDEX idx_game_events_game_turn ON game_events(game_id, turn_number);

COMMENT ON TABLE game_events IS 'Immutable log of all game events';
COMMENT ON COLUMN game_events.event_type IS 'Type of event: roll_dice, buy_property, pay_rent, etc.';
COMMENT ON COLUMN game_events.event_data IS 'JSON payload with event details';

-- ===================
-- UPDATE TRIGGER
-- ===================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER games_updated_at
    BEFORE UPDATE ON games
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ===================
-- HELPER VIEWS
-- ===================

-- View to get active (non-bankrupt) players in a game
CREATE VIEW active_players AS
SELECT p.*, g.status as game_status
FROM players p
JOIN games g ON g.id = p.game_id
WHERE p.is_bankrupt = FALSE;

-- View to get current player for each in-progress game
CREATE VIEW current_players AS
SELECT p.*, g.turn_number
FROM players p
JOIN games g ON g.id = p.game_id
WHERE g.status = 'in_progress'
  AND p.player_order = g.current_player_index
  AND p.is_bankrupt = FALSE;
