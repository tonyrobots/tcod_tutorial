#  This prevents the linter from complaining that the component class has no owner member (it's defined in the entity class init)
#  pylint: disable=no-member

import tcod as libtcod

from game_messages import Message

class Fighter:
    def __init__(self, hp, defense, power):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        
    def take_damage(self, amount):
        results = []
        self.hp -= amount
        
        if self.hp <= 0:
            results.append({'dead': self.owner})
        return results
    
    def heal(self, amount=0):
        results = []
        if amount == 0:
            # heal full if amount is 0
            self.hp = self.max_hp
            results.append({'message': Message('You are restored to full health.')})
        else:
            self.hp += amount
            if self.hp > self.max_hp:
                self.hp = self.max_hp
            results.append({'message': Message('{0} is healed {1} hit point(s).'.format(
                self.owner.name.capitalize(), amount), libtcod.white)})
        return results
    
    
    def attack(self, target):
        results = []
        damage = self.power - target.fighter.defense

        if damage > 0:
            results.append({'message': Message('{0} attacks {1} for {2} hit points.'.format(
                self.owner.name.capitalize(), target.name, str(damage)), libtcod.white)})
            results.extend(target.fighter.take_damage(damage))

        else:
            results.append({'message': Message('{0} attacks {1} but does no damage.'.format(
                self.owner.name.capitalize(), target.name), libtcod.white)})
        return results
        
        
