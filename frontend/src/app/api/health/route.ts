import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET() {
  try {
    const healthData = await apiClient.getHealthStatus();
    return NextResponse.json(healthData);
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        app_name: "Smart Query Reformulation Engine",
        version: "0.1.0",
        environment: process.env.NODE_ENV || "development",
        vector_store: {
          status: "unavailable",
          error: error instanceof Error ? error.message : "Backend unreachable",
        },
      },
      { status: 503 }
    );
  }
}
