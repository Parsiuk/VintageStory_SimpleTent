using System;
using System.Text;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Util;
using Vintagestory.GameContent;

namespace SimpleTent
{
    public class BlockTent : Block, IClaimTraverseable
    {
        // Same limit as the vanilla bed.
        const float MinTirednessToSleep = 8;

        public static IMountableSeat GetMountable(IWorldAccessor world, TreeAttribute tree)
        {
            BlockPos pos = new BlockPos(tree.GetInt("posx"), tree.GetInt("posy"), tree.GetInt("posz"));
            return world.BlockAccessor.GetBlockEntity(pos) as BlockEntityTent;
        }

        // Multiblock filler cells forward interaction here with the position corrected to this block.
        public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
        {
            return byPlayer.Entity.Controls.CtrlKey
                ? TryPickUp(world, byPlayer, blockSel)
                : TrySleep(world, byPlayer, blockSel);
        }

        bool TryPickUp(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
        {
            BlockPos pos = blockSel.Position;
            if (!world.Claims.TryAccess(byPlayer, pos, EnumBlockAccessFlags.BuildOrBreak)) return false;

            if (world.BlockAccessor.GetBlockEntity(pos) is BlockEntityTent tent && tent.MountedBy != null) return false;

            if (world.Side == EnumAppSide.Server && BlockBehaviorReinforcable.AllowRightClickPickup(world, pos, byPlayer))
            {
                ItemStack stack = OnPickBlock(world, pos);
                if (!byPlayer.InventoryManager.TryGiveItemstack(stack, true))
                {
                    world.SpawnItemEntity(stack, byPlayer.Entity.Pos.XYZ);
                }

                world.PlaySoundAt(GetSounds(world.BlockAccessor, blockSel).Place, byPlayer, null);
                world.BlockAccessor.SetBlock(0, pos);
                world.BlockAccessor.TriggerNeighbourBlockUpdate(pos);
            }

            return true;
        }

        bool TrySleep(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
        {
            if (!world.Claims.TryAccess(byPlayer, blockSel.Position, EnumBlockAccessFlags.Use)) return false;

            if (world.BlockAccessor.GetBlockEntity(blockSel.Position) is not BlockEntityTent tent) return false;
            if (tent.MountedBy != null) return false;

            if (byPlayer.Entity.GetBehavior("tiredness") is EntityBehaviorTiredness tiredness && tiredness.Tiredness <= MinTirednessToSleep)
            {
                return RefuseSleep(world, byPlayer, "nottiredenough", "not-tired-enough");
            }

            bool sleepAllowedInStorm = api.World.Config.GetString("temporalStormSleeping", "0").ToInt() != 0;
            if (!sleepAllowedInStorm && api.ModLoader.GetModSystem<SystemTemporalStability>().StormStrength > 0)
            {
                return RefuseSleep(world, byPlayer, "cantsleep-tempstorm", "cantsleep-tempstorm");
            }

            return byPlayer.Entity.TryMount(tent);
        }

        bool RefuseSleep(IWorldAccessor world, IPlayer byPlayer, string errorCode, string langCode)
        {
            if (world.Side == EnumAppSide.Client)
            {
                (api as ICoreClientAPI).TriggerIngameError(this, errorCode, Lang.Get(langCode));
            }
            else
            {
                byPlayer.Entity.TryUnmount();
            }

            return false;
        }

        double SleepHours(IWorldAccessor world)
        {
            return Math.Round(Attributes["sleepEfficiency"].AsDouble(0.5) * world.Calendar.HoursPerDay / 2, 1);
        }

        public override void GetHeldItemInfo(ItemSlot inSlot, StringBuilder dsc, IWorldAccessor world, bool withDebugInfo)
        {
            base.GetHeldItemInfo(inSlot, dsc, world, withDebugInfo);
            dsc.AppendLine("\n" + Lang.Get("Lets you sleep for {0} hours a day", SleepHours(world)));
        }

        public override string GetPlacedBlockInfo(IWorldAccessor world, BlockPos pos, IPlayer forPlayer)
        {
            return base.GetPlacedBlockInfo(world, pos, forPlayer) + Lang.Get("Lets you sleep for up to {0} hours", SleepHours(world));
        }

        public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer)
        {
            return new WorldInteraction[]
            {
                new WorldInteraction()
                {
                    ActionLangCode = "blockhelp-bed-sleep",
                    MouseButton = EnumMouseButton.Right
                },
                new WorldInteraction()
                {
                    ActionLangCode = "blockhelp-behavior-rightclickpickup",
                    HotKeyCode = "ctrl",
                    MouseButton = EnumMouseButton.Right
                }
            }.Append(base.GetPlacedBlockInteractionHelp(world, selection, forPlayer));
        }
    }
}
