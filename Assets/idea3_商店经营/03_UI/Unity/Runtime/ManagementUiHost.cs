using System.Collections.Generic;
using UnityEngine;

namespace OneMoreDiner.ManagementUi
{
    /// <summary>Holds the assembled screens and shows one at a time.
    /// No input handling on purpose: the project decides which keys open what.</summary>
    public class ManagementUiHost : MonoBehaviour
    {
        public List<GameObject> screens = new List<GameObject>();
        public int index;

        private void OnEnable()
        {
            Show(index);
        }

        public void Show(int target)
        {
            if (screens.Count == 0)
            {
                return;
            }
            index = Mathf.Clamp(target, 0, screens.Count - 1);
            for (var i = 0; i < screens.Count; i++)
            {
                var screen = screens[i];
                if (screen != null && screen.activeSelf != (i == index))
                {
                    screen.SetActive(i == index);
                }
            }
        }

        public void Next()
        {
            Show(index + 1);
        }

        public void Previous()
        {
            Show(index - 1);
        }
    }
}
