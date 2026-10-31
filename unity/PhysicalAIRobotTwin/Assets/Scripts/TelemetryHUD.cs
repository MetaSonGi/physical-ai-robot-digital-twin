using System.Text;
using RosMessageTypes.Std;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine;

/// <summary>On-screen dashboard: joint angles, sync error, latency, safety & policy status.</summary>
public class TelemetryHUD : MonoBehaviour
{
    public RobotTwinController twin;
    float syncErr = float.NaN, latency = float.NaN, policyMs = float.NaN;
    string safety = "-", task = "-";
    readonly StringBuilder sb = new StringBuilder();

    void Start()
    {
        var ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<Float32Msg>("/twin/sync_error_rad", m => syncErr = m.data);
        ros.Subscribe<Float32Msg>("/twin/latency_ms", m => latency = m.data);
        ros.Subscribe<Float32Msg>("/policy/latency_ms", m => policyMs = m.data);
        ros.Subscribe<StringMsg>("/safety/status", m => safety = m.data);
        ros.Subscribe<StringMsg>("/task/status", m => task = m.data);
    }

    void OnGUI()
    {
        sb.Clear();
        sb.AppendLine("<b>Physical AI Digital Twin</b>");
        if (twin != null)
        {
            foreach (var kv in twin.LastState) sb.AppendLine($"{kv.Key,-20} {kv.Value * Mathf.Rad2Deg,8:F1}°");
            sb.AppendLine($"msg age        {twin.LastMessageAge * 1000f,8:F0} ms");
        }
        sb.AppendLine($"sync error     {syncErr * Mathf.Rad2Deg,8:F2}°");
        sb.AppendLine($"round-trip     {latency,8:F1} ms");
        sb.AppendLine($"policy infer   {policyMs,8:F2} ms");
        sb.AppendLine($"safety         {safety}");
        sb.AppendLine($"task           {task}");
        var style = new GUIStyle(GUI.skin.box) { alignment = TextAnchor.UpperLeft, richText = true, fontSize = 14 };
        GUI.Box(new Rect(10, 10, 320, 24 + 18 * sb.ToString().Split('\n').Length), sb.ToString(), style);
    }
}
