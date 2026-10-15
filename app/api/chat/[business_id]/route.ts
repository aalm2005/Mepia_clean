import { NextRequest, NextResponse } from "next/server";
import { chatProxy, validChatId } from "@/utils/chat-proxy";
export const dynamic = "force-dynamic";
export async function POST(req: NextRequest, { params }: { params: Promise<{ business_id: string }> }) {
  const { business_id } = await params;
  if (!validChatId(business_id)) return NextResponse.json({ detail: "Negocio inválido" }, { status: 422 });
  return chatProxy(req, `/business/${business_id}/chat`);
}
