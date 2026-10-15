import { NextRequest } from "next/server";
import { chatProxy } from "@/utils/chat-proxy";
export const dynamic = "force-dynamic";
export async function GET(req: NextRequest) { return chatProxy(req, "/me/businesses"); }
