use std::path::Path;

/// Devuelve la raiz del proyecto (donde vive src/core) y la ruta absoluta
/// del script de Python. Basado en CARGO_MANIFEST_DIR (…/src-tauri), cuyo
/// padre es la raiz. Valido para build local del propio usuario.
#[tauri::command]
fn app_paths() -> serde_json::Value {
    let manifest = env!("CARGO_MANIFEST_DIR"); // …/OrquestaGit/src-tauri
    let root = Path::new(manifest)
        .parent()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| manifest.to_string());
    let script = format!("{}/src/core/orquesta_core.py", root);
    serde_json::json!({ "root": root, "script": script })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![app_paths])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
