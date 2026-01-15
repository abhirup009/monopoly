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

export type PropertyDetail = {
  type: "street" | "railroad" | "utility";
  color?: string;
  price: number;
  mortgage: number;
  rent?: number[];
  houseCost?: number;
};

export const PROPERTY_DETAILS: Record<string, PropertyDetail> = {
  mediterranean: {
    type: "street",
    color: "brown",
    price: 60,
    mortgage: 30,
    rent: [2, 10, 30, 90, 160, 250],
    houseCost: 50
  },
  baltic: {
    type: "street",
    color: "brown",
    price: 60,
    mortgage: 30,
    rent: [4, 20, 60, 180, 320, 450],
    houseCost: 50
  },
  oriental: {
    type: "street",
    color: "light_blue",
    price: 100,
    mortgage: 50,
    rent: [6, 30, 90, 270, 400, 550],
    houseCost: 50
  },
  vermont: {
    type: "street",
    color: "light_blue",
    price: 100,
    mortgage: 50,
    rent: [6, 30, 90, 270, 400, 550],
    houseCost: 50
  },
  connecticut: {
    type: "street",
    color: "light_blue",
    price: 120,
    mortgage: 60,
    rent: [8, 40, 100, 300, 450, 600],
    houseCost: 50
  },
  st_charles: {
    type: "street",
    color: "pink",
    price: 140,
    mortgage: 70,
    rent: [10, 50, 150, 450, 625, 750],
    houseCost: 100
  },
  states: {
    type: "street",
    color: "pink",
    price: 140,
    mortgage: 70,
    rent: [10, 50, 150, 450, 625, 750],
    houseCost: 100
  },
  virginia: {
    type: "street",
    color: "pink",
    price: 160,
    mortgage: 80,
    rent: [12, 60, 180, 500, 700, 900],
    houseCost: 100
  },
  st_james: {
    type: "street",
    color: "orange",
    price: 180,
    mortgage: 90,
    rent: [14, 70, 200, 550, 750, 950],
    houseCost: 100
  },
  tennessee: {
    type: "street",
    color: "orange",
    price: 180,
    mortgage: 90,
    rent: [14, 70, 200, 550, 750, 950],
    houseCost: 100
  },
  new_york: {
    type: "street",
    color: "orange",
    price: 200,
    mortgage: 100,
    rent: [16, 80, 220, 600, 800, 1000],
    houseCost: 100
  },
  kentucky: {
    type: "street",
    color: "red",
    price: 220,
    mortgage: 110,
    rent: [18, 90, 250, 700, 875, 1050],
    houseCost: 150
  },
  indiana: {
    type: "street",
    color: "red",
    price: 220,
    mortgage: 110,
    rent: [18, 90, 250, 700, 875, 1050],
    houseCost: 150
  },
  illinois: {
    type: "street",
    color: "red",
    price: 240,
    mortgage: 120,
    rent: [20, 100, 300, 750, 925, 1100],
    houseCost: 150
  },
  atlantic: {
    type: "street",
    color: "yellow",
    price: 260,
    mortgage: 130,
    rent: [22, 110, 330, 800, 975, 1150],
    houseCost: 150
  },
  ventnor: {
    type: "street",
    color: "yellow",
    price: 260,
    mortgage: 130,
    rent: [22, 110, 330, 800, 975, 1150],
    houseCost: 150
  },
  marvin_gardens: {
    type: "street",
    color: "yellow",
    price: 280,
    mortgage: 140,
    rent: [24, 120, 360, 850, 1025, 1200],
    houseCost: 150
  },
  pacific: {
    type: "street",
    color: "green",
    price: 300,
    mortgage: 150,
    rent: [26, 130, 390, 900, 1100, 1275],
    houseCost: 200
  },
  north_carolina: {
    type: "street",
    color: "green",
    price: 300,
    mortgage: 150,
    rent: [26, 130, 390, 900, 1100, 1275],
    houseCost: 200
  },
  pennsylvania: {
    type: "street",
    color: "green",
    price: 320,
    mortgage: 160,
    rent: [28, 150, 450, 1000, 1200, 1400],
    houseCost: 200
  },
  park_place: {
    type: "street",
    color: "dark_blue",
    price: 350,
    mortgage: 175,
    rent: [35, 175, 500, 1100, 1300, 1500],
    houseCost: 200
  },
  boardwalk: {
    type: "street",
    color: "dark_blue",
    price: 400,
    mortgage: 200,
    rent: [50, 200, 600, 1400, 1700, 2000],
    houseCost: 200
  },
  reading_rr: {
    type: "railroad",
    price: 200,
    mortgage: 100,
    rent: [25, 50, 100, 200]
  },
  pennsylvania_rr: {
    type: "railroad",
    price: 200,
    mortgage: 100,
    rent: [25, 50, 100, 200]
  },
  bo_rr: {
    type: "railroad",
    price: 200,
    mortgage: 100,
    rent: [25, 50, 100, 200]
  },
  short_line_rr: {
    type: "railroad",
    price: 200,
    mortgage: 100,
    rent: [25, 50, 100, 200]
  },
  electric_company: {
    type: "utility",
    price: 150,
    mortgage: 75
  },
  water_works: {
    type: "utility",
    price: 150,
    mortgage: 75
  }
};

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
