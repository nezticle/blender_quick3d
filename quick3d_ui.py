import bpy
from . import qtquick3d_mesh


def read_quick3d_mesh(context, filepath, use_some_setting):
    mesh_file = qtquick3d_mesh.MeshFile()
    mesh_file.loadMeshFile(filepath)

    print(mesh_file.meshes)

    base_name = bpy.path.clean_name(bpy.path.display_name_from_filepath(filepath))
    for id,mesh in mesh_file.meshes.items():
        mesh_name = base_name
        if len(mesh_file.meshes) != 1:
            mesh_name = base_name + "_" + id
        # create a new "Mesh"
        bl_mesh = bpy.data.meshes.new(name=mesh_name)
        # fill the mesh with data
        #meshVertices = mesh.vertexBuffer.vertices()
        meshIndexes = mesh.indexBuffer.indexes()
        mesh.vertexBuffer.unpackAttributes()

        vertices = mesh.vertexBuffer.positions
        edges = []
        faces = []

        if mesh.drawMode == 7: # Triangles
            for subset in mesh.subsets:
                index = subset.offset
                while index + 2 < subset.offset + subset.count:
                    face = [ meshIndexes[index], meshIndexes[index + 1], meshIndexes[index + 2] ]
                    faces.append(face)
                    index += 3

        bl_mesh.from_pydata(vertices, edges, faces)
        bl_mesh.update()


        # create a new "Object"
        object = bpy.data.objects.new(name=mesh_name, object_data=bl_mesh)
        # add object to the active collection
        bpy.context.view_layer.active_layer_collection.collection.objects.link(object)
        

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportQuick3DMesh(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_quick3d.mesh"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Quick3D Mesh"

    # ImportHelper mixin class uses this
    filename_ext = ".mesh"

    filter_glob: StringProperty(
        default="*.mesh",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )

    def execute(self, context):
        return read_quick3d_mesh(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportQuick3DMesh.bl_idname, text="Qt Quick 3D (.mesh)")

# Register and add to the "file selector" menu (required to use F3 search "Quick3D Mesh Import" for quick access)
def register():
    bpy.utils.register_class(ImportQuick3DMesh)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportQuick3DMesh)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
