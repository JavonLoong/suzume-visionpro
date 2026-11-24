using Unity.Burst;
using Unity.Jobs;

namespace Unity.Barracuda
{
    // The door network has three nearest-neighbour upscales. BurstCPU previously inherited
    // ReferenceCPUOps' synchronous scalar loops here, forcing unfinished convolution jobs to
    // complete on the render thread. Keep these exact copies in the existing fenced job chain.
    public partial class BurstCPUOps
    {
        public override Tensor Upsample2D(Tensor X, int[] scale, bool bilinear)
        {
            if (bilinear || X.dataType != DataType.Float || !X.shape.Is4D()
                || scale.Length != 2 || scale[0] < 1 || scale[1] < 1)
                return base.Upsample2D(X, scale, bilinear);
            var O = NewOutputTensor(X.dataType, new TensorShape(X.batch,
                X.height * scale[1], X.width * scale[0], X.channels));
            var job = new DoorNearestUpsampleJob {
                channels=X.channels, sourceWidth=X.width, sourceHeight=X.height,
                targetWidth=O.width, targetHeight=O.height, scaleX=scale[0], scaleY=scale[1]
            };
            job.ScheduleXO(Pin(X), Pin(O, uploadCache:false), O.batch * O.height * O.width, 64);
            return O;
        }

        [BurstCompile(OptimizeFor=OptimizeFor.Performance)]
        unsafe struct DoorNearestUpsampleJob : IJobParallelFor, IJobResourceDeclarationXO
        {
            public ReadOnlyMemResource X { get; set; }
            public ReadWriteMemResource O { get; set; }
            public int channels, sourceWidth, sourceHeight, targetWidth, targetHeight, scaleX, scaleY;
            public void Execute(int pixel)
            {
                int x = pixel % targetWidth;
                int by = pixel / targetWidth;
                int y = by % targetHeight, b = by / targetHeight;
                int source = ((b * sourceHeight + y / scaleY) * sourceWidth + x / scaleX) * channels;
                int target = pixel * channels;
                for(int c=0;c<channels;c++) O.ptrfloat[target+c] = X.ptrfloat[source+c];
            }
        }
    }
}
