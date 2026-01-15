export type GameState = {
  id: string;
  status: string;
  current_player_index: number;
  turn_number: number;
  turn_phase: string;
  last_dice_roll: number[] | null;
  players: PlayerState[];
  properties: PropertyState[];
  winner_id?: string | null;
};

export type PlayerState = {
  id: string;
  name: string;
  model: string;
  personality: string;
  player_order: number;
  position: number;
  cash: number;
  in_jail: boolean;
  jail_turns: number;
  get_out_of_jail_cards: number;
  is_bankrupt: boolean;
};

export type PropertyState = {
  property_id: string;
  owner_id: string | null;
  houses: number;
};

export type SocketJoinResponse = {
  success: boolean;
  game_id: string;
  state: GameState | null;
  error?: string;
};

export type TurnActionEvent = {
  game_id: string;
  player_id: string;
  player_name: string;
  action: {
    type: string;
    property_id?: string | null;
  };
  result: {
    success: boolean;
    message: string;
    dice_roll?: number[];
    new_position?: number;
    amount_paid?: number;
    amount_received?: number;
  };
};

export type AgentDecisionEvent = {
  game_id: string;
  player_id: string;
  player_name: string;
  action: {
    type: string;
    property_id?: string | null;
  };
  reasoning?: string;
};

export type PlayerMovedEvent = {
  game_id: string;
  player_id: string;
  player_name: string;
  from_position: number;
  to_position: number;
  dice_total?: number;
};
