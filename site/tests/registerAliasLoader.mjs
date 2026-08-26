/*
 * Registers the "@/..." alias resolver for node --test runs. Import this
 * module BEFORE any dynamic import of an @-aliased source module.
 */
import { register } from "node:module";
register("./aliasLoader.mjs", import.meta.url);
