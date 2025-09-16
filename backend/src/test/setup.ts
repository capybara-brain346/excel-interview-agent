import { config } from "@/config/env";

beforeAll(async () => {
  process.env.NODE_ENV = "test";
});

afterAll(async () => {});
