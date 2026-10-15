import { NextRequest, NextResponse } from "next/server";
import { chatProxy, validChatId } from "@/utils/chat-proxy";
export const dynamic = "force-dynamic";
async function forward(req: NextRequest, { params }: { params: Promise<{ business_id: string; conversation_id: string }> }) {
  const { business_id, conversation_id } = await params;
  if (!validChatId(business_id) || !validChatId(conversation_id)) {
    return NextResponse.json({ detail: "Conversación inválida" }, { status: 422 });
  }
  return chatProxy(req, `/business/${business_id}/chat/${conversation_id}`);
}
export const GET = forward;
export const DELETE = forward;
