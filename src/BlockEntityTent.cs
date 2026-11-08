using System.Reflection;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace SimpleTent
{
    /// <summary>
    /// The tent's bed. It must be a BlockEntityBed because the game only plays the eyes-closing
    /// overlay for that type. Only the seat position differs, so the interfaces are re-implemented
    /// to replace it.
    /// </summary>
    public class BlockEntityTent : BlockEntityBed, IMountableSeat, IMountable
    {
        public const string MountableClassName = "simpletent-tent";

        // The vanilla bed reads this when the sleeper wakes, but derives it from a compass
        // direction in the block code, which a tent doesn't have.
        static readonly FieldInfo FeetFacingField = typeof(BlockEntityBed).GetField("facing", BindingFlags.Instance | BindingFlags.NonPublic);

        readonly EntityPos mountPos = new EntityPos();

        double seatX = 0.5, seatY, seatZ = 0.5;
        float seatYaw;

        public new EntityPos SeatPosition => Position;
        public new EntityPos Position
        {
            get
            {
                mountPos.SetPos(Pos);
                mountPos.Yaw = seatYaw;
                return mountPos.Add(seatX, seatY, seatZ);
            }
        }

        public override void Initialize(ICoreAPI api)
        {
            // Must come first: the base call remounts a player who logged out asleep, which reads the seat.
            LoadSeatPose();

            base.Initialize(api);

            FeetFacingField.SetValue(this, Block.Variant["orientation"] == "we" ? BlockFacing.EAST : BlockFacing.SOUTH);
        }

        // bedPose is written by tools/build.py from the hay_bed element, for the block's unrotated "ns" shape.
        void LoadSeatPose()
        {
            JsonObject pose = Block.Attributes["bedPose"];
            double x = pose["x"].AsDouble(0.5);
            double z = pose["z"].AsDouble(0.5);
            float yawDeg = pose["yawDeg"].AsFloat(0);
            seatY = pose["y"].AsDouble(0);

            if (Block.Variant["orientation"] == "we")
            {
                // Matches rotateY: 90 on the "we" shape.
                (x, z) = (z, 1 - x);
                yawDeg += 90;
            }

            seatX = x;
            seatZ = z;
            seatYaw = yawDeg * GameMath.DEG2RAD;
        }

        public new void MountableToTreeAttributes(TreeAttribute tree)
        {
            base.MountableToTreeAttributes(tree);
            tree.SetString("className", MountableClassName);
        }
    }
}
