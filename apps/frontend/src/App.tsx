import { useEffect, useMemo, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";

import {
  BOARD_GRID,
  BOARD_SPACES,
  PROPERTY_COLOR_BY_ID,
  PROPERTY_DETAILS,
  PROPERTY_NAME_BY_ID
} from "./board";
import {
  AgentDecisionEvent,
  GameState,
  PlayerMovedEvent,
  SocketJoinResponse,
  TurnActionEvent
} from "./types";

const PLAYER_COLORS = [
  "#ff8c66",
  "#78c6ff",
  "#9bffb4",
  "#ffd36a",
  "#c39cff",
  "#ff7ad9"
];

const DEFAULT_AGENTS = [
  { name: "Baron Von Moneybags", personality: "aggressive", model: "llama3.1:8b" },
  { name: "Professor Pennypincher", personality: "analytical", model: "llama3.1:8b" },
  { name: "Lady Luck", personality: "chaotic", model: "llama3.1:8b" }
];

const apiBaseUrl =
  import.meta.env.VITE_ORCHESTRATOR_HTTP_URL ||
  import.meta.env.VITE_ORCHESTRATOR_URL ||
  "http://localhost:3000";

const socketBaseUrl =
  import.meta.env.VITE_ORCHESTRATOR_WS_URL ||
  import.meta.env.VITE_ORCHESTRATOR_URL ||
  "http://localhost:3000";

type LogEntry = {
  id: string;
  message: string;
  tone?: "info" | "warn" | "error";
};

type DiceRoll = {
  dice: [number, number];
  total: number;
  playerName: string;
  isDoubles: boolean;
};

type MoneyFlow = {
  id: string;
  from: string;
  to: string;
  amount: number;
  context: string;
};

export default function App() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [gameIdInput, setGameIdInput] = useState("");
  const [gameId, setGameId] = useState<string | null>(null);
  const [connection, setConnection] = useState<"disconnected" | "connecting" | "connected">(
    "disconnected"
  );
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [speed, setSpeed] = useState<"fast" | "normal" | "slow" | "watch">("normal");
  const [isCreating, setIsCreating] = useState(false);
  const [lastDice, setLastDice] = useState<DiceRoll | null>(null);
  const [moneyFlow, setMoneyFlow] = useState<MoneyFlow | null>(null);
  const socketRef = useRef<Socket | null>(null);

  const sortedPlayers = useMemo(() => {
    if (!gameState?.players) {
      return [];
    }
    return [...gameState.players].sort((a, b) => a.player_order - b.player_order);
  }, [gameState]);

  const playerColorMap = useMemo(() => {
    const map = new Map<string, string>();
    sortedPlayers.forEach((player, index) => {
      map.set(player.id, PLAYER_COLORS[index % PLAYER_COLORS.length]);
    });
    return map;
  }, [sortedPlayers]);

  const propertyStateById = useMemo(() => {
    const map = new Map<string, { owner_id: string | null; houses: number }>();
    gameState?.properties?.forEach((property) => {
      map.set(property.property_id, property);
    });
    return map;
  }, [gameState]);

  const propertyCountByOwner = useMemo(() => {
    const map = new Map<string, number>();
    gameState?.properties?.forEach((property) => {
      if (!property.owner_id) {
        return;
      }
      map.set(property.owner_id, (map.get(property.owner_id) || 0) + 1);
    });
    return map;
  }, [gameState]);

  const propertiesByOwner = useMemo(() => {
    const map = new Map<string, string[]>();
    gameState?.properties?.forEach((property) => {
      if (!property.owner_id) {
        return;
      }
      const list = map.get(property.owner_id) || [];
      list.push(property.property_id);
      map.set(property.owner_id, list);
    });
    return map;
  }, [gameState]);

  const currentPlayer = useMemo(() => {
    if (!gameState) {
      return null;
    }
    return gameState.players[gameState.current_player_index] || null;
  }, [gameState]);

  const announceMoneyFlow = (flow: Omit<MoneyFlow, "id">) => {
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setMoneyFlow({ id, ...flow });
    window.setTimeout(() => {
      setMoneyFlow((prev) => (prev?.id === id ? null : prev));
    }, 2400);
  };

  const pushLog = (message: string, tone: LogEntry["tone"] = "info") => {
    setLogs((prev) => {
      const entry = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        message,
        tone
      };
      return [entry, ...prev].slice(0, 150);
    });
  };

  const formatRentSummary = (propertyId: string) => {
    const detail = PROPERTY_DETAILS[propertyId];
    if (!detail) {
      return "Rent: --";
    }
    if (detail.type === "utility") {
      return "Rent: 4x dice (1 utility) / 10x dice (2 utilities)";
    }
    if (detail.type === "railroad") {
      return "Rent: 25 / 50 / 100 / 200 (1-4 railroads)";
    }
    if (!detail.rent) {
      return "Rent: --";
    }
    return `Rent: ${detail.rent.join(" / ")}`;
  };

  const formatPropertyLabel = (propertyId: string) => {
    const name = PROPERTY_NAME_BY_ID[propertyId] || propertyId;
    const detail = PROPERTY_DETAILS[propertyId];
    if (!detail) {
      return name;
    }
    return `${name} ($${detail.price})`;
  };

  const renderPropertyCard = (propertyId: string) => {
    const detail = PROPERTY_DETAILS[propertyId];
    const name = PROPERTY_NAME_BY_ID[propertyId] || propertyId;
    if (!detail) {
      return null;
    }

    if (detail.type === "utility") {
      return (
        <div className="property-card">
          <div className="property-card-header">
            <h3>{name}</h3>
            <span className="property-type">Utility</span>
          </div>
          <div className="property-meta">
            <span>Price: ${detail.price}</span>
            <span>Mortgage: ${detail.mortgage}</span>
          </div>
          <div className="property-rent-grid">
            <div>Rent (1 utility)</div>
            <div>4x dice roll</div>
            <div>Rent (2 utilities)</div>
            <div>10x dice roll</div>
          </div>
        </div>
      );
    }

    if (detail.type === "railroad") {
      return (
        <div className="property-card">
          <div className="property-card-header">
            <h3>{name}</h3>
            <span className="property-type">Railroad</span>
          </div>
          <div className="property-meta">
            <span>Price: ${detail.price}</span>
            <span>Mortgage: ${detail.mortgage}</span>
          </div>
          <div className="property-rent-grid">
            <div>Rent (1 RR)</div>
            <div>${detail.rent?.[0] ?? "--"}</div>
            <div>Rent (2 RR)</div>
            <div>${detail.rent?.[1] ?? "--"}</div>
            <div>Rent (3 RR)</div>
            <div>${detail.rent?.[2] ?? "--"}</div>
            <div>Rent (4 RR)</div>
            <div>${detail.rent?.[3] ?? "--"}</div>
          </div>
        </div>
      );
    }

    const baseRent = detail.rent?.[0] ?? 0;
    return (
      <div className="property-card">
        <div className="property-card-header">
          <h3>{name}</h3>
          <span className="property-type">Property</span>
        </div>
        <div className="property-meta">
          <span>Price: ${detail.price}</span>
          <span>Mortgage: ${detail.mortgage}</span>
        </div>
        <div className="property-rent-grid">
          <div>Rent</div>
          <div>${baseRent}</div>
          <div>With Color Set</div>
          <div>${baseRent * 2}</div>
          <div>With 1 House</div>
          <div>${detail.rent?.[1] ?? "--"}</div>
          <div>With 2 Houses</div>
          <div>${detail.rent?.[2] ?? "--"}</div>
          <div>With 3 Houses</div>
          <div>${detail.rent?.[3] ?? "--"}</div>
          <div>With 4 Houses</div>
          <div>${detail.rent?.[4] ?? "--"}</div>
          <div>With Hotel</div>
          <div>${detail.rent?.[5] ?? "--"}</div>
        </div>
        {detail.houseCost ? (
          <div className="property-meta">
            <span>House Cost: ${detail.houseCost}</span>
            <span>Hotel Cost: ${detail.houseCost}</span>
          </div>
        ) : null}
      </div>
    );
  };

  useEffect(() => {
    if (!gameId) {
      return;
    }

    setConnection("connecting");
    const socket = io(socketBaseUrl, {
      transports: ["websocket"],
      autoConnect: true
    });
    socketRef.current = socket;

    socket.on("connect", () => {
      setConnection("connected");
      socket.emit("join_game", { game_id: gameId }, (response: SocketJoinResponse) => {
        if (!response?.success) {
          pushLog(response?.error || "Failed to join game.", "error");
          return;
        }
        if (response.state) {
          setGameState(response.state);
        }
        pushLog(`Watching game ${response.game_id}.`);
      });
    });

    socket.on("disconnect", () => {
      setConnection("disconnected");
      pushLog("Disconnected from orchestrator.", "warn");
    });

    socket.on("game:state", (payload: { game_id: string; state: GameState }) => {
      if (payload?.state) {
        setGameState(payload.state);
      }
    });

    socket.on("game:started", (payload: { game_id: string }) => {
      pushLog(`Game ${payload.game_id} started.`);
    });

    socket.on("game:ended", (payload: { game_id: string; winner_name: string }) => {
      pushLog(`Game ended. Winner: ${payload.winner_name}.`, "warn");
    });

    socket.on("game:error", (payload: { error: string }) => {
      pushLog(`Game error: ${payload.error}`, "error");
    });

    socket.on("turn:start", (payload: { player_name: string; turn_number: number }) => {
      pushLog(`Turn ${payload.turn_number} started for ${payload.player_name}.`);
    });

    socket.on("turn:end", (payload: { player_name: string; turn_number: number }) => {
      pushLog(`Turn ${payload.turn_number} ended for ${payload.player_name}.`);
    });

    socket.on("turn:action", (payload: TurnActionEvent) => {
      if (payload?.result?.message) {
        pushLog(payload.result.message);
      } else if (payload?.action?.type) {
        pushLog(`${payload.player_name} executed ${payload.action.type}.`);
      }
      if (payload?.result?.amount_paid) {
        announceMoneyFlow({
          from: payload.player_name,
          to: payload.action?.type === "pay_jail_fine" ? "Bank" : "Owner",
          amount: payload.result.amount_paid,
          context: payload.action?.type || "payment"
        });
      } else if (payload?.result?.amount_received) {
        announceMoneyFlow({
          from: "Bank",
          to: payload.player_name,
          amount: payload.result.amount_received,
          context: payload.action?.type || "payout"
        });
      }
    });

    socket.on("agent:thinking", (payload: { player_name: string; phase: string }) => {
      pushLog(`${payload.player_name} is thinking (${payload.phase}).`);
    });

    socket.on("agent:decision", (payload: AgentDecisionEvent) => {
      const detail = payload.reasoning ? ` Reason: ${payload.reasoning}` : "";
      pushLog(`${payload.player_name} decided ${payload.action.type}.${detail}`);
    });

    socket.on("dice:rolled", (payload: { player_name: string; total: number; dice?: [number, number] }) => {
      const dice = payload.dice || [Math.ceil(payload.total / 2), Math.floor(payload.total / 2)];
      const isDoubles = dice[0] === dice[1];
      setLastDice({
        dice: dice as [number, number],
        total: payload.total,
        playerName: payload.player_name,
        isDoubles
      });
      pushLog(`${payload.player_name} rolled ${dice[0]} + ${dice[1]} = ${payload.total}${isDoubles ? " (DOUBLES!)" : ""}`);
    });

    socket.on("player:moved", (payload: PlayerMovedEvent) => {
      pushLog(
        `${payload.player_name} moved from ${payload.from_position} to ${payload.to_position}.`
      );
    });

    socket.on("property:purchased", (payload: { player_name: string; property_id: string }) => {
      const name = PROPERTY_NAME_BY_ID[payload.property_id] || payload.property_id;
      pushLog(`${payload.player_name} purchased ${name}.`);
    });

    socket.on("property:passed", (payload: { player_name: string; property_id: string }) => {
      const name = PROPERTY_NAME_BY_ID[payload.property_id] || payload.property_id;
      pushLog(`${payload.player_name} passed on ${name}.`);
    });

    socket.on("rent:paid", (payload: { player_name: string; amount: number }) => {
      pushLog(`${payload.player_name} paid rent of $${payload.amount}.`);
      announceMoneyFlow({
        from: payload.player_name,
        to: "Owner",
        amount: payload.amount,
        context: "rent"
      });
    });

    socket.on("card:drawn", (payload: { player_name: string; card_text: string }) => {
      pushLog(`${payload.player_name} drew a card: ${payload.card_text}`);
    });

    socket.on("building:built", (payload: { player_name: string; property_id: string }) => {
      const name = PROPERTY_NAME_BY_ID[payload.property_id] || payload.property_id;
      pushLog(`${payload.player_name} built on ${name}.`);
    });

    socket.on("jail:action", (payload: { player_name: string; action_type: string }) => {
      pushLog(`${payload.player_name} jail action: ${payload.action_type}.`);
    });

    return () => {
      socket.disconnect();
    };
  }, [gameId]);

  const handleJoin = () => {
    if (!gameIdInput.trim()) {
      pushLog("Enter a game id to join.", "warn");
      return;
    }
    setLogs([]);
    setGameState(null);
    setGameId(gameIdInput.trim());
  };

  const handleCreateGame = async () => {
    setIsCreating(true);
    try {
      const response = await fetch(`${apiBaseUrl}/games`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agents: DEFAULT_AGENTS,
          settings: { speed, turn_timeout: 30 }
        })
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Failed to create game.");
      }

      const data = (await response.json()) as { game_id: string };
      setLogs([]);
      setGameState(null);
      setGameId(data.game_id);
      setGameIdInput(data.game_id);
      pushLog(`Created game ${data.game_id}.`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      pushLog(`Create game failed: ${message}`, "error");
    } finally {
      setIsCreating(false);
    }
  };

  const handleSpeedChange = (nextSpeed: "fast" | "normal" | "slow" | "watch") => {
    setSpeed(nextSpeed);
    if (!gameId || !socketRef.current) {
      return;
    }
    socketRef.current.emit("set_speed", { game_id: gameId, speed: nextSpeed }, (resp: any) => {
      if (!resp?.success) {
        pushLog(resp?.error || "Failed to set speed.", "warn");
      }
    });
  };

  const handleStopGame = async () => {
    if (!gameId) {
      pushLog("No active game to stop.", "warn");
      return;
    }
    try {
      const response = await fetch(`${apiBaseUrl}/games/${gameId}/stop`, {
        method: "POST"
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Failed to stop game.");
      }
      pushLog(`Game ${gameId} stopped.`, "warn");
      setLastDice(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      pushLog(`Stop game failed: ${message}`, "error");
    }
  };

  return (
    <div className="app">
      <div className="ambient" />

      <header className="topbar">
        <div>
          <h1>AI Monopoly Arena</h1>
        </div>
        <div className="status">
          <div>
            <p className="label">Turn</p>
            <p className="value">{gameState?.turn_number ?? "--"}</p>
          </div>
          <div>
            <p className="label">Now Playing</p>
            <p className="value">{currentPlayer?.name ?? "--"}</p>
          </div>
          <div>
            <p className="label">Phase</p>
            <p className="value">{gameState?.turn_phase ?? "waiting"}</p>
          </div>
          <div>
            <p className="label">Speed</p>
            <div className="segmented">
              {(["fast", "normal", "slow", "watch"] as const).map((option) => (
                <button
                  key={option}
                  className={speed === option ? "active" : ""}
                  type="button"
                  onClick={() => handleSpeedChange(option)}
                  disabled={!gameId}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
          <div className="bank-chip">
            <span className="bank-logo">$</span>
            <div>
              <p className="label">Bank</p>
              <p className="value">Monopoly</p>
            </div>
          </div>
        </div>
      </header>

      <main className="layout">
        <section className="panel board-panel">
          <div className="panel-header">
            <h2>Live Board</h2>
            <span className="pill">Socket.IO · {gameId ? `game ${gameId}` : "waiting"}</span>
          </div>
          <div className="board">
            {BOARD_GRID.map((space, index) => {
              if (!space) {
                return <div key={`empty-${index}`} className="cell empty" />;
              }

              const propertyState = space.property_id
                ? propertyStateById.get(space.property_id)
                : null;
              const ownerColor = propertyState?.owner_id
                ? playerColorMap.get(propertyState.owner_id) || ""
                : "";
              const ownerName = propertyState?.owner_id
                ? sortedPlayers.find((player) => player.id === propertyState.owner_id)?.name
                : null;
              const bandColor = space.property_id
                ? PROPERTY_COLOR_BY_ID[space.property_id] || ""
                : "";
              const tokens = sortedPlayers.filter(
                (player) => player.position === space.position && !player.is_bankrupt
              );
              const getInitials = (name: string) =>
                name
                  .split(" ")
                  .filter(Boolean)
                  .slice(0, 2)
                  .map((part) => part[0])
                  .join("");

              return (
                <div
                  key={`tile-${index}`}
                  className="cell tile"
                  style={ownerColor ? { borderColor: ownerColor } : undefined}
                >
                  {bandColor ? (
                    <div className="color-band" style={{ background: bandColor }} />
                  ) : null}
                  <div className="tile-name">{space.name}</div>
                  <div className="tile-type">{space.type.replace(/_/g, " ")}</div>
                  {ownerName ? (
                    <div className="owner-pill" style={{ background: ownerColor }}>
                      {ownerName.split(" ")[0]}
                    </div>
                  ) : (
                    <div className="owner-pill neutral">Unowned</div>
                  )}
                  {propertyState?.houses ? (
                    <div className="house-count">Houses: {propertyState.houses}</div>
                  ) : null}
                  <div className="token-stack">
                    {tokens.map((token) => (
                      <span
                        key={token.id}
                        className="token"
                        style={{ background: playerColorMap.get(token.id) }}
                        title={token.name}
                      >
                        <span className="token-label">{getInitials(token.name)}</span>
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
            <div className="board-center">
              <div>
                {lastDice ? (
                  <div className="dice-widget">
                    <p className="center-eyebrow">Last Roll</p>
                    <div className="dice-values">
                      <span className="die">{lastDice.dice[0]}</span>
                      <span className="die">{lastDice.dice[1]}</span>
                      <span className="dice-total">= {lastDice.total}</span>
                    </div>
                    <p className="center-subtitle">
                      {lastDice.playerName}
                      {lastDice.isDoubles ? " · DOUBLES!" : ""}
                    </p>
                  </div>
                ) : (
                  <>
                    <p className="center-eyebrow">Live Feed</p>
                    <h3>{connection === "connected" ? "Connected" : "Idle"}</h3>
                    <p className="center-subtitle">
                      {gameId ? "Streaming turn events." : "Create or join a game."}
                    </p>
                  </>
                )}
                {moneyFlow ? (
                  <div className="money-flow">
                    <div className="money-row">
                      <span className="money-from">{moneyFlow.from}</span>
                      <span className="money-arrow">→</span>
                      <span className="money-to">{moneyFlow.to}</span>
                    </div>
                    <div className="money-amount">${moneyFlow.amount}</div>
                    <div className="money-context">{moneyFlow.context}</div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
          <div className="legend">
            {sortedPlayers.length === 0 ? (
              <span className="muted">Awaiting players.</span>
            ) : (
              sortedPlayers.map((player) => (
                <div className="legend-item" key={player.id}>
                  <span
                    className="dot"
                    style={{ background: playerColorMap.get(player.id) }}
                  />
                  {player.name}
                </div>
              ))
            )}
          </div>
        </section>

        <aside className="right-rail">
          <section className="panel control-panel">
            <div className="panel-header">
              <h2>Game Control</h2>
              <span className={`pill ${connection}`}>{connection}</span>
            </div>
            <div className="control-grid">
              <label>
                <span>Game ID</span>
                <input
                  value={gameIdInput}
                  onChange={(event) => setGameIdInput(event.target.value)}
                  placeholder="Enter game id"
                />
              </label>
              <div className="control-actions">
                <button type="button" onClick={handleJoin}>
                  Join game
                </button>
                <button type="button" onClick={handleCreateGame} disabled={isCreating}>
                  {isCreating ? "Creating..." : "Start new game"}
                </button>
                <button
                  type="button"
                  className="stop-btn"
                  onClick={handleStopGame}
                  disabled={!gameId || gameState?.status === "completed"}
                >
                  Stop game
                </button>
              </div>
              <div className="control-meta">
                <p>API: {apiBaseUrl}</p>
                <p>Socket: {socketBaseUrl}</p>
              </div>
            </div>
          </section>

          <section className="panel" id="players">
            <div className="panel-header">
              <h2>Agents</h2>
              <span className="pill">{sortedPlayers.length} active</span>
            </div>
            <div className="player-list">
              {sortedPlayers.map((player, index) => (
                <div
                  key={player.id}
                  className={`player-card ${
                    gameState?.current_player_index === index ? "active" : ""
                  }`}
                  style={{
                    borderColor: playerColorMap.get(player.id),
                    boxShadow: `0 12px 30px ${playerColorMap.get(player.id)}20`
                  }}
                >
                  <header>
                    <span className="player-name">
                      <span
                        className="player-color-dot"
                        style={{ background: playerColorMap.get(player.id) }}
                      />
                      {player.name}
                    </span>
                    <span className="tag">{player.personality}</span>
                  </header>
                  <div className="player-meta">
                    <span>{player.model}</span>
                    <span>Pos {player.position}</span>
                  </div>
                  <div className="player-stats">
                    <span>Cash: ${player.cash.toLocaleString()}</span>
                    <span>Props: {propertyCountByOwner.get(player.id) || 0}</span>
                  </div>
                  <details className="property-details">
                    <summary>
                      Properties ({propertyCountByOwner.get(player.id) || 0})
                    </summary>
                    <div className="property-mini-grid">
                      {(propertiesByOwner.get(player.id) || []).map((propertyId) => (
                        <div key={propertyId} className="property-mini-card">
                          <div className="property-mini-title">
                            <span
                              className="mini-color"
                              style={{
                                background: PROPERTY_COLOR_BY_ID[propertyId] || "#2a3444"
                              }}
                            />
                            <strong>{PROPERTY_NAME_BY_ID[propertyId] || propertyId}</strong>
                          </div>
                          <div className="property-mini-meta">
                            {formatPropertyLabel(propertyId)}
                          </div>
                          <div className="property-mini-rent">
                            {formatRentSummary(propertyId)}
                          </div>
                        </div>
                      ))}
                      {(propertiesByOwner.get(player.id) || []).length === 0 && (
                        <div className="muted">No properties yet.</div>
                      )}
                    </div>
                  </details>
                </div>
              ))}
            </div>
          </section>

          <section className="panel chat-panel">
            <div className="panel-header">
              <h2>Action Log</h2>
              <span className="pill">streaming</span>
            </div>
            <div className="chat-feed">
              {logs.length === 0 ? (
                <div className="chat-message">
                  <strong>System</strong>
                  <span>No events yet. Start or join a game.</span>
                </div>
              ) : (
                logs.map((entry) => (
                  <div key={entry.id} className={`chat-message ${entry.tone || ""}`}>
                    <strong>{entry.tone || "info"}</strong>
                    <span>{entry.message}</span>
                  </div>
                ))
              )}
            </div>
          </section>
        </aside>
      </main>

      <section className="panel log-panel">
        <div className="panel-header">
          <h2>Property Intel</h2>
          <span className="pill">{BOARD_SPACES.length} tiles</span>
        </div>
        <div className="property-cards">
          {BOARD_SPACES.filter((space) => space.property_id).map((space) => {
            const ownerId = space.property_id
              ? propertyStateById.get(space.property_id)?.owner_id
              : null;
            const ownerName = ownerId
              ? sortedPlayers.find((player) => player.id === ownerId)?.name
              : "Unowned";
            const bandColor = space.property_id
              ? PROPERTY_COLOR_BY_ID[space.property_id] || ""
              : "";
            return (
              <div key={space.position} className="property-card-wrap">
                <div
                  className="property-card-band"
                  style={{ background: bandColor || "#2a3444" }}
                />
                <div className="property-owner">Owner: {ownerName}</div>
                {space.property_id ? renderPropertyCard(space.property_id) : null}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
