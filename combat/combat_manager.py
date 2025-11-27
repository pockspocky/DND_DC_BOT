"""Combat Manager - Handles core logic management for D&D combat"""
import discord
from typing import Optional, List, Dict, Any
from database import db_manager
from dice.advanced_roller import advanced_roller
import logging

logger = logging.getLogger(__name__)

class CombatParticipant:
    """Combat participant data class"""
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.name = data.get('name') or ""
        self.initiative = data.get('initiative') or 0
        self.current_hp = data.get('current_hp') or 0
        self.max_hp = data.get('max_hp') or 0
        self.armor_class = data.get('armor_class', 10)
        self.is_npc = data.get('is_npc', False)
        self.position_in_turn = data.get('position_in_turn') or 0
        
    @property
    def hp_percentage(self) -> float:
        """HP percentage"""
        if self.max_hp <= 0:
            return 0.0
        return (self.current_hp / self.max_hp) * 100
    
    @property
    def status_icon(self) -> str:
        """Return status icon based on HP"""
        if self.current_hp <= 0:
            return "💀"
        elif self.hp_percentage <= 25:
            return "🔴"
        elif self.hp_percentage <= 50:
            return "🟡"
        else:
            return "🟢"
    
    @property
    def type_icon(self) -> str:
        """Character type icon"""
        return "🤖" if self.is_npc else "🎭"

class CombatSession:
    """Combat session data class"""
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.guild_id = data.get('guild_id')
        self.channel_id = data.get('channel_id')
        self.dm_user_id = data.get('dm_user_id')
        self.name = data.get('name') or ""
        self.current_turn = data.get('current_turn', 0)
        self.current_round = data.get('current_round', 1)
        self.status = data.get('status', 'active')
        self.participants: List[CombatParticipant] = []

class CombatManager:
    """Combat manager main class"""
    
    def __init__(self):
        self.dice_roller = advanced_roller
        
    async def is_dm(self, user: discord.Member) -> bool:
        """Check if user has DM permissions"""
        dm_roles = ["DM", "dm", "Dm", "dM"]
        user_roles = [role.name for role in user.roles]
        has_dm_role = any(role in dm_roles for role in user_roles)
        has_admin = user.guild_permissions.administrator
        return has_dm_role or has_admin
    
    async def get_active_combat(self, guild_id: int, channel_id: int) -> Optional[CombatSession]:
        """Get active combat in current channel"""
        query = """
            SELECT * FROM combat_sessions 
            WHERE guild_id = ? AND channel_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        """
        
        try:
            result = await db_manager.fetchone(query, (guild_id, channel_id))
            if result:
                combat = CombatSession(dict(result))
                combat.participants = await self.get_participants(combat.id)
                return combat
            return None
        except Exception as e:
            logger.error(f"Failed to get active combat: {e}")
            return None
    
    async def start_combat(self, guild_id: int, channel_id: int, dm_user_id: int, name: str) -> Optional[CombatSession]:
        """Start a new combat session"""
        existing_combat = await self.get_active_combat(guild_id, channel_id)
        if existing_combat:
            return None
        
        query = """
            INSERT INTO combat_sessions (guild_id, channel_id, dm_user_id, name)
            VALUES (?, ?, ?, ?)
        """
        
        try:
            cursor = await db_manager.execute(query, (guild_id, channel_id, dm_user_id, name))
            session_id = cursor.lastrowid
            
            if session_id:
                await self.log_combat_action(
                    session_id, 1, 0, "combat_start", "System", None,
                    f"Combat '{name}' started", None, None
                )
                
                result = await db_manager.fetchone(
                    "SELECT * FROM combat_sessions WHERE id = ?", (session_id,)
                )
                if result:
                    return CombatSession(dict(result))
            return None
            
        except Exception as e:
            logger.error(f"Failed to create combat session: {e}")
            return None
    
    async def end_combat(self, session_id: int) -> bool:
        """End combat session"""
        query = """
            UPDATE combat_sessions 
            SET status = 'ended', ended_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """
        
        try:
            await db_manager.execute(query, (session_id,))
            await self.log_combat_action(
                session_id, 0, 0, "combat_end", "System", None,
                "Combat ended", None, None
            )
            return True
        except Exception as e:
            logger.error(f"Failed to end combat: {e}")
            return False
    
    async def add_participant(
        self, session_id: int, name: str, max_hp: int, 
        initiative: int, ac: int = 10, is_npc: bool = False
    ) -> Optional[CombatParticipant]:
        """Add combat participant"""
        try:
            existing = await db_manager.fetchone(
                "SELECT id FROM combat_participants WHERE combat_session_id = ? AND name = ?",
                (session_id, name)
            )
            if existing:
                return None
            
            position = await self._calculate_turn_position(session_id, initiative)
            
            query = """
                INSERT INTO combat_participants 
                (combat_session_id, name, initiative, current_hp, max_hp, armor_class, is_npc, position_in_turn)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor = await db_manager.execute(
                query, (session_id, name, initiative, max_hp, max_hp, ac, is_npc, position)
            )
            participant_id = cursor.lastrowid
            
            if participant_id:
                await self.log_combat_action(
                    session_id, 1, position, "add_participant", "System", name,
                    f"{'NPC' if is_npc else 'Character'} {name} joined combat (Initiative: {initiative}, HP: {max_hp}, AC: {ac})",
                    None, None
                )
                
                await self._reorder_participants(session_id)
                
                result = await db_manager.fetchone(
                    "SELECT * FROM combat_participants WHERE id = ?", (participant_id,)
                )
                if result:
                    return CombatParticipant(dict(result))
            return None
            
        except Exception as e:
            logger.error(f"Failed to add participant: {e}")
            return None
    
    async def get_participants(self, session_id: int) -> List[CombatParticipant]:
        """Get list of combat participants"""
        query = """
            SELECT * FROM combat_participants 
            WHERE combat_session_id = ? AND is_active = 1
            ORDER BY position_in_turn
        """
        
        try:
            results = await db_manager.fetchall(query, (session_id,))
            return [CombatParticipant(dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Failed to get participants: {e}")
            return []

    async def remove_participant(self, session_id: int, name: str) -> bool:
        """Remove combat participant"""
        try:
            # Check if participant exists
            participant = await self._get_participant_by_name(session_id, name)
            if not participant:
                return False
            
            # Mark participant as inactive
            query = """
                UPDATE combat_participants 
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE combat_session_id = ? AND name = ?
            """
            
            await db_manager.execute(query, (session_id, name))
            
            # Log combat action
            await self.log_combat_action(
                session_id, 1, participant.position_in_turn, "remove_participant", "System", name,
                f"{participant.type_icon} {name} left combat"
            )
            
            # Reorder remaining participants
            await self._reorder_participants(session_id)
            
            # Adjust current turn (if removed character was in current turn)
            await self._adjust_current_turn_after_removal(session_id, participant.position_in_turn)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove participant: {e}")
            return False
    
    async def next_turn(self, session_id: int) -> Optional[CombatParticipant]:
        """Advance to next turn"""
        combat = await self._get_combat_by_id(session_id)
        if not combat:
            return None
        
        participants = await self.get_participants(session_id)
        if not participants:
            return None
        
        next_turn = (combat.current_turn + 1) % len(participants)
        next_round = combat.current_round
        
        if next_turn == 0 and combat.current_turn != 0:
            next_round += 1
        
        query = """
            UPDATE combat_sessions 
            SET current_turn = ?, current_round = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        
        try:
            await db_manager.execute(query, (next_turn, next_round, session_id))
            
            current_participant = participants[next_turn]
            
            await self.log_combat_action(
                session_id, next_round, next_turn, "turn_change", "System", current_participant.name,
                f"Round {next_round} - {current_participant.name}'s turn",
                None, None
            )
            
            return current_participant
            
        except Exception as e:
            logger.error(f"Failed to advance turn: {e}")
            return None
    
    async def apply_damage(
        self, session_id: int, target_name: str, damage: int, 
        attacker_name: str = "Unknown", dice_expr: str = None, dice_result: str = None
    ) -> Optional[CombatParticipant]:
        """Deal damage to target"""
        participant = await self._get_participant_by_name(session_id, target_name)
        if not participant:
            return None
        
        old_hp = participant.current_hp
        new_hp = max(0, old_hp - damage)
        is_death = new_hp == 0 and old_hp > 0
        
        query = """
            UPDATE combat_participants 
            SET current_hp = ?, updated_at = CURRENT_TIMESTAMP
            WHERE combat_session_id = ? AND name = ?
        """
        
        try:
            await db_manager.execute(query, (new_hp, session_id, target_name))
            
            action_desc = f"{attacker_name} dealt {damage} damage to {target_name}"
            if is_death:
                action_desc += f" - {target_name} is down!"
            
            await self.log_combat_action(
                session_id, participant.position_in_turn, participant.position_in_turn,
                "damage", attacker_name, target_name, action_desc,
                dice_expr, dice_result, damage, 0, old_hp, new_hp, False, is_death
            )
            
            participant.current_hp = new_hp
            return participant
            
        except Exception as e:
            logger.error(f"Failed to apply damage: {e}")
            return None
    
    async def apply_healing(
        self, session_id: int, target_name: str, healing: int,
        healer_name: str = "Unknown", dice_expr: str = None, dice_result: str = None
    ) -> Optional[CombatParticipant]:
        """Heal target"""
        participant = await self._get_participant_by_name(session_id, target_name)
        if not participant:
            return None
        
        old_hp = participant.current_hp
        new_hp = min(participant.max_hp, old_hp + healing)
        actual_healing = new_hp - old_hp
        
        query = """
            UPDATE combat_participants 
            SET current_hp = ?, updated_at = CURRENT_TIMESTAMP
            WHERE combat_session_id = ? AND name = ?
        """
        
        try:
            await db_manager.execute(query, (new_hp, session_id, target_name))
            
            await self.log_combat_action(
                session_id, participant.position_in_turn, participant.position_in_turn,
                "healing", healer_name, target_name,
                f"{healer_name} healed {target_name} for {actual_healing} HP",
                dice_expr, dice_result, 0, actual_healing, old_hp, new_hp
            )
            
            participant.current_hp = new_hp
            return participant
            
        except Exception as e:
            logger.error(f"Failed to apply healing: {e}")
            return None
    
    async def log_combat_action(
        self, session_id: int, round_num: int, turn_order: int,
        action_type: str, actor_name: str, target_name: Optional[str],
        description: str, dice_expr: Optional[str] = None, dice_result: Optional[str] = None,
        damage: int = 0, healing: int = 0, hp_before: Optional[int] = None,
        hp_after: Optional[int] = None, is_critical: bool = False, is_death: bool = False
    ) -> bool:
        """Log combat action"""
        query = """
            INSERT INTO combat_logs 
            (combat_session_id, round_number, turn_order, action_type, actor_name, target_name,
             action_description, dice_expression, dice_result, damage_dealt, healing_dealt,
             hp_before, hp_after, is_critical, is_death)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            await db_manager.execute(query, (
                session_id, round_num, turn_order, action_type, actor_name, target_name,
                description, dice_expr, dice_result, damage, healing,
                hp_before, hp_after, is_critical, is_death
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to log combat action: {e}")
            return False
    
    async def _calculate_turn_position(self, session_id: int, initiative: int) -> int:
        """Calculate turn position for new participant"""
        participants = await self.get_participants(session_id)
        position = 0
        for participant in participants:
            if participant.initiative >= initiative:
                position += 1
            else:
                break
        return position
    
    async def _reorder_participants(self, session_id: int) -> bool:
        """Reorder participant turn positions"""
        try:
            participants = await db_manager.fetchall(
                "SELECT id, initiative FROM combat_participants WHERE combat_session_id = ? ORDER BY initiative DESC, id ASC",
                (session_id,)
            )
            
            for position, participant in enumerate(participants):
                await db_manager.execute(
                    "UPDATE combat_participants SET position_in_turn = ? WHERE id = ?",
                    (position, participant['id'])
                )
            return True
        except Exception as e:
            logger.error(f"Failed to reorder participants: {e}")
            return False
    
    async def _get_combat_by_id(self, session_id: int) -> Optional[CombatSession]:
        """Get combat session by ID"""
        try:
            result = await db_manager.fetchone(
                "SELECT * FROM combat_sessions WHERE id = ?", (session_id,)
            )
            if result:
                return CombatSession(dict(result))
            return None
        except Exception as e:
            logger.error(f"Failed to get combat session: {e}")
            return None
    
    async def _get_participant_by_name(self, session_id: int, name: str) -> Optional[CombatParticipant]:
        """Get participant by name"""
        try:
            result = await db_manager.fetchone(
                "SELECT * FROM combat_participants WHERE combat_session_id = ? AND name = ? AND is_active = 1",
                (session_id, name)
            )
            if result:
                return CombatParticipant(dict(result))
            return None
        except Exception as e:
            logger.error(f"Failed to get participant: {e}")
            return None

    async def _adjust_current_turn_after_removal(self, session_id: int, removed_position: int) -> bool:
        """Adjust current turn after participant removal"""
        try:
            combat = await self._get_combat_by_id(session_id)
            if not combat:
                return False
            
            participants = await self.get_participants(session_id)
            if not participants:
                # No more participants, reset turn
                await db_manager.execute(
                    "UPDATE combat_sessions SET current_turn = 0 WHERE id = ?",
                    (session_id,)
                )
                return True
            
            # If removed character was before current turn, adjust current turn index
            new_turn = combat.current_turn
            if removed_position <= combat.current_turn:
                new_turn = max(0, combat.current_turn - 1)
            
            # Ensure turn index doesn't exceed range
            if new_turn >= len(participants):
                new_turn = 0
            
            await db_manager.execute(
                "UPDATE combat_sessions SET current_turn = ? WHERE id = ?",
                (new_turn, session_id)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to adjust turn: {e}")
            return False
