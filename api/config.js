module.exports = function handler(request, response) {
  response.setHeader("content-type", "application/json; charset=utf-8");
  response.status(200).json({
    mode: process.env.NOMAD_DASHBOARD_MODE || "local",
    supabaseUrl: process.env.VITE_SUPABASE_URL || "",
    supabaseAnonKey: process.env.VITE_SUPABASE_ANON_KEY || ""
  });
};
