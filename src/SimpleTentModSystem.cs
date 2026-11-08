using Vintagestory.API.Common;

namespace SimpleTent
{
    public class SimpleTentModSystem : ModSystem
    {
        public override void Start(ICoreAPI api)
        {
            base.Start(api);

            api.RegisterBlockClass("simpletent.Tent", typeof(BlockTent));
            api.RegisterBlockEntityClass("simpletent.Tent", typeof(BlockEntityTent));
            api.RegisterMountable(BlockEntityTent.MountableClassName, BlockTent.GetMountable);
        }
    }
}
