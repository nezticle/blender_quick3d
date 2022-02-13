# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Qt Quick 3D Tools",
    "author" : "Andy Nichols",
    "description" : "",
    "blender" : (3, 0, 1),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Import-Export"
}

if "bpy" in locals():
    import importlib
    importlib.reload(qtquick3d_mesh)
    importlib.reload(quick3d_ui)
else:
    from . import qtquick3d_mesh
    from . import quick3d_ui
import bpy

def register():
    quick3d_ui.register()

def unregister():
    quick3d_ui.unregister()

if __name__ == "__main__":
    register()