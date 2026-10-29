using Ryujinx.Graphics.Shader.Decoders;
using Ryujinx.Graphics.Shader.IntermediateRepresentation;
using Ryujinx.Graphics.Shader.Translation;

using static Ryujinx.Graphics.Shader.Instructions.InstEmitHelper;
using static Ryujinx.Graphics.Shader.IntermediateRepresentation.OperandHelper;

namespace Ryujinx.Graphics.Shader.Instructions
{
    // PRMT (byte permute), added for NX2Apple (upstream Ryujinx leaves it unimplemented): Rd byte i = byte sel_i of the 8 bytes {Ra bytes 0-3, Rc bytes 4-7}.
    // Default mode: selector nibble i of Sb, bits 0-2 the byte index, bit 3 replicates that byte's sign bit. Other modes take a 2-bit index from Sb and a fixed pattern (as PTX prmt.f4e / b4e / rc8 / ecl / ecr / rc16).
    // EA SPORTS FC 27's tile light grid vertex shader (0332490f5224b266) packs its light indices with it: without it the lights covered the wrong tiles of the career scenes.
    static partial class InstEmit
    {
        public static void PrmtR(EmitterContext context)
        {
            InstPrmtR op = context.GetOp<InstPrmtR>();
            EmitPrmt(context, GetSrcReg(context, op.SrcA), GetSrcReg(context, op.SrcB), GetSrcReg(context, op.SrcC), op.Dest, op.PMode);
        }

        public static void PrmtI(EmitterContext context)
        {
            InstPrmtI op = context.GetOp<InstPrmtI>();
            EmitPrmt(context, GetSrcReg(context, op.SrcA), GetSrcImm(context, Imm20ToSInt(op.Imm20)), GetSrcReg(context, op.SrcC), op.Dest, op.PMode);
        }

        public static void PrmtC(EmitterContext context)
        {
            InstPrmtC op = context.GetOp<InstPrmtC>();
            EmitPrmt(context, GetSrcReg(context, op.SrcA), GetSrcCbuf(context, op.CbufSlot, op.CbufOffset), GetSrcReg(context, op.SrcC), op.Dest, op.PMode);
        }

        public static void PrmtRc(EmitterContext context)
        {
            InstPrmtRc op = context.GetOp<InstPrmtRc>();
            EmitPrmt(context, GetSrcReg(context, op.SrcA), GetSrcReg(context, op.SrcC), GetSrcCbuf(context, op.CbufSlot, op.CbufOffset), op.Dest, op.PMode);
        }

        // Fixed patterns of the non-default modes, by 2-bit index: nibbles = source byte of result bytes 0..3 (PTX's table, read from byte 0 up)
        private static readonly int[][] PrmtPatterns =
        {
            null,
            new[] { 0x3210, 0x4321, 0x5432, 0x6543 }, // F4e
            new[] { 0x5670, 0x6701, 0x7012, 0x0123 }, // B4e (PTX lists them byte 3 first)
            new[] { 0x0000, 0x1111, 0x2222, 0x3333 }, // Rc8
            new[] { 0x3210, 0x3211, 0x3222, 0x3333 }, // Ecl
            new[] { 0x0000, 0x1110, 0x2210, 0x3210 }, // Ecr
            new[] { 0x1010, 0x3232, 0x1010, 0x3232 }, // Rc16
        };

        private static void EmitPrmt(EmitterContext context, Operand srcA, Operand srcB, Operand srcC, int rd, PMode mode)
        {
            Operand sel = srcB;
            bool signRep = true;
            int m = (int)mode;

            if (m >= 1 && m <= 6)
            {
                // PTX writes these patterns as d.b3 d.b2 d.b1 d.b0: nibble 0 of each constant is result byte 0
                int[] pat = PrmtPatterns[m];
                Operand idx = context.BitwiseAnd(srcB, Const(3));
                sel = Const(pat[3]);
                for (int k = 2; k >= 0; k--)
                {
                    sel = context.ConditionalSelect(context.ICompareEqual(idx, Const(k)), Const(pat[k]), sel);
                }
                signRep = false;
            }

            Operand res = Const(0);

            for (int i = 0; i < 4; i++)
            {
                Operand nib = context.BitfieldExtractU32(sel, Const(i * 4), Const(4));
                Operand byteIdx = context.BitwiseAnd(nib, Const(7));
                Operand fromA = context.ICompareLessUnsigned(byteIdx, Const(4));
                Operand src = context.ConditionalSelect(fromA, srcA, srcC);
                Operand shift = context.ShiftLeft(context.BitwiseAnd(byteIdx, Const(3)), Const(3));
                Operand b = context.BitwiseAnd(context.ShiftRightU32(src, shift), Const(0xff));

                if (signRep)
                {
                    Operand rep = context.ICompareNotEqual(context.BitwiseAnd(nib, Const(8)), Const(0));
                    Operand signFill = context.BitwiseAnd(context.BitfieldExtractS32(b, Const(7), Const(1)), Const(0xff));
                    b = context.ConditionalSelect(rep, signFill, b);
                }

                res = context.BitwiseOr(res, context.ShiftLeft(b, Const(i * 8)));
            }

            context.Copy(GetDest(rd), res);
        }
    }
}
