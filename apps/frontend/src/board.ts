export type BoardSpace = {
  position: number;
  name: string;
  type: string;
  property_id?: string;
  amount?: number;
};

export const BOARD_SPACES: BoardSpace[] = [
  { position: 0, name: "GO", type: "go" },
  { position: 1, name: "Mediterranean Avenue", type: "property", property_id: "mediterranean" },
  { position: 2, name: "Community Chest", type: "community_chest" },
  { position: 3, name: "Baltic Avenue", type: "property", property_id: "baltic" },
  { position: 4, name: "Income Tax", type: "tax", amount: 200 },
  { position: 5, name: "Reading Railroad", type: "property", property_id: "reading_rr" },
  { position: 6, name: "Oriental Avenue", type: "property", property_id: "oriental" },
  { position: 7, name: "Chance", type: "chance" },
  { position: 8, name: "Vermont Avenue", type: "property", property_id: "vermont" },
  { position: 9, name: "Connecticut Avenue", type: "property", property_id: "connecticut" },
  { position: 10, name: "Jail / Just Visiting", type: "jail" },
  { position: 11, name: "St. Charles Place", type: "property", property_id: "st_charles" },
  { position: 12, name: "Electric Company", type: "property", property_id: "electric_company" },
  { position: 13, name: "States Avenue", type: "property", property_id: "states" },
  { position: 14, name: "Virginia Avenue", type: "property", property_id: "virginia" },
  { position: 15, name: "Pennsylvania Railroad", type: "property", property_id: "pennsylvania_rr" },
  { position: 16, name: "St. James Place", type: "property", property_id: "st_james" },
  { position: 17, name: "Community Chest", type: "community_chest" },
  { position: 18, name: "Tennessee Avenue", type: "property", property_id: "tennessee" },
  { position: 19, name: "New York Avenue", type: "property", property_id: "new_york" },
  { position: 20, name: "Free Parking", type: "free_parking" },
  { position: 21, name: "Kentucky Avenue", type: "property", property_id: "kentucky" },
  { position: 22, name: "Chance", type: "chance" },
  { position: 23, name: "Indiana Avenue", type: "property", property_id: "indiana" },
  { position: 24, name: "Illinois Avenue", type: "property", property_id: "illinois" },
  { position: 25, name: "B&O Railroad", type: "property", property_id: "bo_rr" },
  { position: 26, name: "Atlantic Avenue", type: "property", property_id: "atlantic" },
  { position: 27, name: "Ventnor Avenue", type: "property", property_id: "ventnor" },
  { position: 28, name: "Water Works", type: "property", property_id: "water_works" },
  { position: 29, name: "Marvin Gardens", type: "property", property_id: "marvin_gardens" },
  { position: 30, name: "Go To Jail", type: "go_to_jail" },
  { position: 31, name: "Pacific Avenue", type: "property", property_id: "pacific" },
  { position: 32, name: "North Carolina Avenue", type: "property", property_id: "north_carolina" },
  { position: 33, name: "Community Chest", type: "community_chest" },
  { position: 34, name: "Pennsylvania Avenue", type: "property", property_id: "pennsylvania" },
  { position: 35, name: "Short Line Railroad", type: "property", property_id: "short_line_rr" },
  { position: 36, name: "Chance", type: "chance" },
  { position: 37, name: "Park Place", type: "property", property_id: "park_place" },
  { position: 38, name: "Luxury Tax", type: "tax", amount: 100 },
  { position: 39, name: "Boardwalk", type: "property", property_id: "boardwalk" }
];

export const PROPERTY_COLORS: Record<string, string> = {
  brown: "#8d6b4f",
  light_blue: "#7cb8ff",
  pink: "#ff8ccf",
  orange: "#f0c86a",
  red: "#ff7a7a",
  yellow: "#ffd36a",
  green: "#5ae4a8",
  dark_blue: "#78c6ff",
  railroad: "#9098a7",
  utility: "#7de2ff"
};

export const PROPERTY_COLOR_BY_ID: Record<string, string> = {
  mediterranean: PROPERTY_COLORS.brown,
  baltic: PROPERTY_COLORS.brown,
  oriental: PROPERTY_COLORS.light_blue,
  vermont: PROPERTY_COLORS.light_blue,
  connecticut: PROPERTY_COLORS.light_blue,
  st_charles: PROPERTY_COLORS.pink,
  states: PROPERTY_COLORS.pink,
  virginia: PROPERTY_COLORS.pink,
  st_james: PROPERTY_COLORS.orange,
  tennessee: PROPERTY_COLORS.orange,
  new_york: PROPERTY_COLORS.orange,
  kentucky: PROPERTY_COLORS.red,
  indiana: PROPERTY_COLORS.red,
  illinois: PROPERTY_COLORS.red,
  atlantic: PROPERTY_COLORS.yellow,
  ventnor: PROPERTY_COLORS.yellow,
  marvin_gardens: PROPERTY_COLORS.yellow,
  pacific: PROPERTY_COLORS.green,
  north_carolina: PROPERTY_COLORS.green,
  pennsylvania: PROPERTY_COLORS.green,
  park_place: PROPERTY_COLORS.dark_blue,
  boardwalk: PROPERTY_COLORS.dark_blue,
  reading_rr: PROPERTY_COLORS.railroad,
  pennsylvania_rr: PROPERTY_COLORS.railroad,
  bo_rr: PROPERTY_COLORS.railroad,
  short_line_rr: PROPERTY_COLORS.railroad,
  electric_company: PROPERTY_COLORS.utility,
  water_works: PROPERTY_COLORS.utility
};

export const PROPERTY_NAME_BY_ID: Record<string, string> = BOARD_SPACES.reduce(
  (acc, space) => {
    if (space.property_id) {
      acc[space.property_id] = space.name;
    }
    return acc;
  },
  {} as Record<string, string>
);

const BOARD_SIZE = 11;

export const BOARD_GRID: (BoardSpace | null)[] = (() => {
  const grid = new Array(BOARD_SIZE * BOARD_SIZE).fill(null);
  let index = 0;
  const last = BOARD_SIZE - 1;

  for (let col = last; col >= 0; col -= 1) {
    grid[last * BOARD_SIZE + col] = BOARD_SPACES[index];
    index += 1;
  }

  for (let row = last - 1; row > 0; row -= 1) {
    grid[row * BOARD_SIZE] = BOARD_SPACES[index];
    index += 1;
  }

  for (let col = 0; col < BOARD_SIZE; col += 1) {
    grid[col] = BOARD_SPACES[index];
    index += 1;
  }

  for (let row = 1; row < last; row += 1) {
    grid[row * BOARD_SIZE + last] = BOARD_SPACES[index];
    index += 1;
  }

  return grid;
})();
