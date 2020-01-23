import tcod
import tdl
import colors
from random import randint

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

# Map constants
MAP_WIDTH = 80
MAP_HEIGHT = 45
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3 

# Field of view stuff
FOV_ALGO = 'BASIC'  #default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# colors
color_dark_wall = (0, 0, 100)
color_light_wall = (130, 110, 50)
color_dark_ground = (50, 50, 150)
color_light_ground = (200, 180, 50)

class Tile:
    # a tile of the map
    def __init__(self, blocked, block_sight= None):
        self.blocked = blocked
        self.explored=False

        # by default, if tile is blocked, also block sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

class Rect:
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)
 
    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class GameObject:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False):
        self.name = name
        self.blocks = blocks
        self.x = x
        self.y = y
        self.char = char
        self.color = color
 
    def move(self, dx, dy):
        #move by the given amount, if not blocked
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
 
    def draw(self):
        global visible_tiles
        #draw the character that represents this object at its position
        if (self.x, self.y) in visible_tiles:
            con.draw_char(self.x, self.y, self.char, self.color)

 
    def clear(self):
        #erase the character that represents this object
        con.draw_char(self.x, self.y, ' ', self.color, bg=None)



# Initialize stuff
tdl.set_font('assets/consolas12x12_gs_tc.png', greyscale=True, altLayout=True)

root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Roguelike", fullscreen=False)
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)


def make_map():
    global my_map
 
    #fill map with "unblocked" tiles
    my_map = [[ Tile(True)
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]

    rooms = []
    num_rooms = 0
 
    for _ in range(MAX_ROOMS):
        #random width and height
        w = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = randint(0, MAP_WIDTH-w-1)
        y = randint(0, MAP_HEIGHT-h-1)

        new_room = Rect(x, y, w, h)

        # check for intersections

        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
        
        
        if not failed:
        #this means there are no intersections, so this room is valid

            #"paint" it to the map's tiles
            create_room(new_room)

            #center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                #this is the first room, where the player starts at
                player.x = new_x
                player.y = new_y
            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel
 
                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()
 
                #draw a coin (random number that is either 0 or 1)
                if randint(0, 1):
                    #first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
 
            #finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1

            #optional: print "room number" to see how the map drawing worked
            #          we may have more than ten rooms, so print 'A' for the first room, 'B' for the next...
            # room_no = GameObject(new_x, new_y, "room label", chr(65+num_rooms), colors.white)
            # objects.insert(0, room_no) #draw early, so monsters are drawn on top
            


def render_all():
 
    global fov_recompute
    global visible_tiles

    if fov_recompute:
        #recompute FOV if needed (the player moved or something)
        fov_recompute = False
        visible_tiles = tdl.map.quickFOV(player.x, player.y,
                                         is_visible_tile,
                                         fov=FOV_ALGO,
                                         radius=TORCH_RADIUS,
                                         lightWalls=FOV_LIGHT_WALLS)

    #go through all tiles, and set their background color according to the FOV
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            visible = (x, y) in visible_tiles
            wall = my_map[x][y].block_sight
            if not visible:
                #it's out of the player's FOV
                #if it's not visible right now, the player can only see it if it's explored
                if my_map[x][y].explored:
                    if wall:
                        con.draw_char(x, y, None, fg=None, bg=color_dark_wall)
                    else:
                        con.draw_char(x, y, None, fg=None, bg=color_dark_ground)
            else:
                #it's visible
                if wall:
                    con.draw_char(x, y, None, fg=None, bg=color_light_wall)
                else:
                    con.draw_char(x, y, None, fg=None, bg=color_light_ground)
                my_map[x][y].explored = True

    # #draw all objects in the list
    for obj in objects:
        obj.draw()

    #blit the contents of "con" to the root console and present it
    root.blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)

def create_room(room):
    global my_map
    #go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            my_map[x][y].blocked = False
            my_map[x][y].block_sight = False
    place_objects(room)

def place_objects(room):
    num_monsters = randint(0, MAX_ROOM_MONSTERS)

    for _ in range (num_monsters):
        # choose random spot for this monster
        x = randint(room.x1, room.x2)
        y = randint(room.y1, room.y2)

        #only place it if the tile is not blocked
        if not is_blocked(x, y):

            if randint(0,100) < 80:
                # create an orc
                monster = GameObject(x, y, 'o', "Orc", colors.desaturated_green, True)
            else:
                # create a troll
                monster = GameObject(x, y, 'T', "Troll", colors.darker_green, True)
            objects.append(monster)


def create_h_tunnel(x1, x2, y):
    global my_map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    global my_map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False

def is_visible_tile (x,y):
    global my_map
 
    if x >= MAP_WIDTH or x < 0:
        return False
    elif y >= MAP_HEIGHT or y < 0:
        return False
    elif my_map[x][y].blocked == True:
        return False
    elif my_map[x][y].block_sight == True:
        return False
    else:
        return True

def is_blocked(x, y):
    #first test the map tile
    if my_map[x][y].blocked:
        return True
 
    #now check for any blocking objects
    for obj in objects:
        if obj.blocks and obj.x == x and obj.y == y:
            return True
 
    return False

def handle_keys():
    global fov_recompute
    user_input = tdl.event.key_wait()

    if user_input.key == 'ENTER' and user_input.alt:
        #Alt+Enter: toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        return True  #exit game
    #movement keys
    if user_input.key == 'UP':
        player.move(0,-1)
        fov_recompute = True

    elif user_input.key == 'DOWN':
        player.move(0,1)
        fov_recompute = True

    elif user_input.key == 'LEFT':
        player.move(-1,0)
        fov_recompute = True

    elif user_input.key == 'RIGHT':
        player.move(1,0)
        fov_recompute = True

# Initialize game objects
player = GameObject(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, '@', "Player", colors.white, True)
objects = [player]
make_map()


fov_recompute = True

# Main loop
while not tdl.event.is_window_closed():

    render_all()

    tdl.flush()

    # erase all objects at old locations before they move
    for obj in objects:
        obj.clear()
    
    #handle keys and exit game if needed
    exit_game = handle_keys()
    if exit_game:
        break





