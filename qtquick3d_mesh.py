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

import sys
import struct

def alignmentHelper(size):
    #intentionally stupid to match file format
    return bytearray(4 - size % 4)

class Mesh:
    class MeshDataHeader:
        def __init__(self):
            self.fileId = 0
            self.fileVersion = 0
            self.headerFlags = 0
            self.sizeInBytes = 0

        def isValid(self):
            return self.fileId == 3365961549 and self.fileVersion >= 3
        def save(self):
            outputBuffer = struct.pack("<I", self.fileId)
            outputBuffer += struct.pack("<H", self.fileVersion)
            outputBuffer += struct.pack("<H", self.headerFlags)
            outputBuffer += struct.pack("<I", self.sizeInBytes)
            return outputBuffer, 12

    class MeshOffsetTracker:
        startOffset = 0
        byteCounter = 0
        def __init__(self, startOffset):
            self.startOffset = startOffset
        def offset(self):
            return self.startOffset + self.byteCounter
        def alignedAdvance(self, advanceAmount):
            self.advance(advanceAmount)
            alignmentAmount = 4 - (self.byteCounter % 4)
            self.byteCounter += alignmentAmount
        def advance(self, advanceAmount):
            self.byteCounter += advanceAmount

    class VertexBufferEntry:
        def __init__(self):
            self.componentType = 0
            self.numComponents = 0
            self.firstItemOffset = 0
            self.name = ""
        def getFormatString(self):
            formatString = "<"
            formatLetter = ''
            if self.componentType == 1: # uint8 
                formatLetter = 'B'
            elif self.componentType == 2: # int8
                formatLetter = 'b'
            elif self.componentType == 3: # uint16
                formatLetter = 'H'
            elif self.componentType == 4: # int16
                formatLetter = 'h'
            elif self.componentType == 5: # uint32
                formatLetter = "I"
            elif self.componentType == 6: # int32
                formatLetter = "i"
            elif self.componentType == 7: # uin64
                formatLetter = "Q"
            elif self.componentType == 8: # int64
                formatLetter = "q"
            elif self.componentType == 9: # float16
                formatLetter = "e"
            elif self.componentType == 10: #float32
                formatLetter = "f"
            elif self.componentType == 11: #float64
                formatLetter = "d"
            else:
                formatLetter = "f"
            for i in range(self.numComponents):
                formatString += formatLetter
            return formatString

    class VertexBuffer:
        def __init__(self):
            self.stride = 0
            self.entires = []
            self.data = []  
            self.positions = []
            self.normals = []
            self.uv0 = []
            self.uv1 = []
            self.tangents = []
            self.binormals = []
            self.joints = []
            self.weights = []
            self.colors = []

        def unpackAttributes(self):
            # cleanup any old data
            self.positions = []
            self.normals = []
            self.uv0 = []
            self.uv1 = []
            self.tangents = []
            self.binormals = []
            self.joints = []
            self.weights = []
            self.colors = []

            size = len(self.data) // self.stride
            for index in range(size):
                for entry in self.entires:
                    offset = self.stride * index + entry.firstItemOffset
                    value = struct.unpack_from(entry.getFormatString(), self.data, offset)
                    if entry.name == 'attr_pos\x00':
                        self.positions.append(value)
                    elif entry.name == 'attr_norm\x00':
                        self.normals.append(value)
                    elif entry.name == 'attr_uv0\x00':
                        self.uv0.append(value)
                    elif entry.name == 'attr_uv1\x00':
                        self.uv1.append(value)
                    elif entry.name == 'attr_textan\x00':
                        self.tangents.append(value)
                    elif entry.name == 'attr_binormal\x00':
                        self.binormals.append(value)
                    elif entry.name == 'attr_joints\x00':
                        self.joints.append(value)
                    elif entry.name == 'attr_weights\x00':
                        self.weights.append(value)
                    elif entry.name == 'attr_colors\x00':
                        self.colors.append(value)

        def vertices(self):
            vertices = []
            # vertices is a list of dictionaries containing all enrties for that index
            size = len(self.data) // self.stride
            for index in range(size):
                vertex = {}
                for entry in self.entires:
                    offset = self.stride * index + entry.firstItemOffset
                    vertex[entry.name] = struct.unpack_from(entry.getFormatString(), self.data, offset)
                vertices.append(vertex)
            return vertices

    class IndexBuffer:
        def __init__(self):
            self.componentType = 0
            self.data = []
        def indexes(self):
            # This really should only ever be Uint16 or Uint32
            indexes = []
            if self.componentType == 3: # uint16
                dataSize = 2
                size = len(self.data) // dataSize
                for i in range(size):
                    index, = struct.unpack_from("<H", self.data, i * dataSize)
                    indexes.append(index)
            elif self.componentType == 5: # uint32
                dataSize = 4
                size = len(self.data) // dataSize
                for i in range(size):
                    index, = struct.unpack_from("<I", self.data, i * dataSize)
                    indexes.append(index)

            return indexes
        def setIndexes(self, indexArray, componentType):
            # this method packs the data buffer from an array of ints
            type = "<I"
            if componentType == 3:
                type = "<H"
            data = bytearray()
            for index in indexArray:
                data += struct.pack(type, index)
            self.data = data
            self.componentType = componentType



    class MeshSubset:
        class MeshBounds:
            def __init__(self):
                self.minimum = {'x': 0.0, 'y': 0.0, 'z': 0.0}
                self.maximum = {'x': 0.0, 'y': 0.0, 'z': 0.0}
            def printBounds(self):
                print(f"\tbounds: \n\t\tmin: ({self.minimum['x']}, {self.minimum['y']}, {self.minimum['z']}) \n\t\tmax: ({self.maximum['x']}, {self.maximum['y']}, {self.maximum['z']})")
        def __init__(self):
            self.count = 0
            self.offset = 0
            self.bounds = self.MeshBounds()
            self.name = ""
            self.nameLength = 0
            self.lightmapSizeHintWidth = 0
            self.lightmapSizeHintHeight = 0

    class Joint:
        def __init__(self):
            self.jointId = 0
            self.parentId = 0
            self.invBindPos = [1, 0, 0, 0,
                               0, 1, 0, 0,
                               0, 0, 1, 0,
                               0, 0, 0, 1]
            self.localToGlobalBoneSpace = [1, 0, 0, 0,
                                           0, 1, 0, 0,
                                           0, 0, 1, 0,
                                           0, 0, 0, 1]

    def __init__(self):
        self.meshInfo = self.MeshDataHeader()
        self.vertexBuffer = self.VertexBuffer()
        self.indexBuffer = self.IndexBuffer()
        self.subsets = []
        self.joints = []  
    def loadMesh(self, inputFile, offset):
        try:
            with open(inputFile, "rb") as meshFile:
                meshFile.seek(offset)
                # Read the mesh file header
                self.meshInfo.fileId, = struct.unpack("<I", meshFile.read(4))
                self.meshInfo.fileVersion, = struct.unpack("<H", meshFile.read(2))
                self.meshInfo.headerFlags, = struct.unpack("<H", meshFile.read(2))
                self.meshInfo.sizeInBytes, = struct.unpack("<I", meshFile.read(4))

                if not self.meshInfo.isValid():
                    # not valid mesh data
                    meshFile.close()
                    print("File does not contain valid mesh data:", inputFile)
                    return
                # Offset Tracker starts after MeshHeaderData
                offsetTracker = self.MeshOffsetTracker(offset + 12)
                meshFile.seek(offsetTracker.offset())
                # Vertex Buffer
                vertexBufferEntriesOffset, = struct.unpack("<I", meshFile.read(4))
                vertexBufferEntriesSize, = struct.unpack("<I", meshFile.read(4))
                self.vertexBuffer.stride, = struct.unpack("<I", meshFile.read(4))
                vertexBufferDataOffset, = struct.unpack("<I", meshFile.read(4))
                vertexBufferDataSize, = struct.unpack("<I", meshFile.read(4))
                # Index Buffer
                self.indexBuffer.componentType, = struct.unpack("<I", meshFile.read(4))
                indexBufferDataOffset, = struct.unpack("<I", meshFile.read(4))
                indexBufferDataSize, = struct.unpack("<I", meshFile.read(4))
                # Subsets
                subsetsOffsets, = struct.unpack("<I", meshFile.read(4))
                subsetsSize, = struct.unpack("<I", meshFile.read(4))
                # Joints
                jointsOffsets, = struct.unpack("<I", meshFile.read(4))
                jointsSize, = struct.unpack("<I", meshFile.read(4))

                self.drawMode, = struct.unpack("<I", meshFile.read(4))
                self.winding, = struct.unpack("<I", meshFile.read(4))
                # advance offset tracker by sizeof Mesh struct
                offsetTracker.advance(56)
                # Vertex Buffer entries
                entriesByteSize = 0
                for entryIndex in range(vertexBufferEntriesSize):
                    vertexBufferEntry = self.VertexBufferEntry()
                    nameOffset, = struct.unpack("<I", meshFile.read(4))
                    vertexBufferEntry.componentType, = struct.unpack("<I", meshFile.read(4))
                    vertexBufferEntry.numComponents, = struct.unpack("<I", meshFile.read(4))
                    vertexBufferEntry.firstItemOffset, = struct.unpack("<I", meshFile.read(4));
                    entriesByteSize += 16
                    self.vertexBuffer.entires.append(vertexBufferEntry)
                # align after reading entires
                offsetTracker.alignedAdvance(entriesByteSize)
                meshFile.seek(offsetTracker.offset())
                for entry in self.vertexBuffer.entires:
                    nameLength, = struct.unpack("<I", meshFile.read(4))
                    offsetTracker.advance(4)
                    unpackFormat = "<" + str(nameLength) + "s"
                    entry.name = struct.unpack(unpackFormat, meshFile.read(nameLength))[0].decode('utf-8')
                    # get things aligned again if needed
                    offsetTracker.alignedAdvance(nameLength)
                    meshFile.seek(offsetTracker.offset())
                
                # Vertex Buffer Data
                self.vertexBuffer.data = meshFile.read(vertexBufferDataSize)
                offsetTracker.alignedAdvance(vertexBufferDataSize)
                meshFile.seek(offsetTracker.offset())

                # Index Buffer Data
                self.indexBuffer.data = meshFile.read(indexBufferDataSize)
                offsetTracker.alignedAdvance(indexBufferDataSize)
                meshFile.seek(offsetTracker.offset())

                # Subsets
                subsetByteSize = 0
                for subsetIndex in range(subsetsSize):
                    subset = self.MeshSubset()
                    subset.count, = struct.unpack("<I", meshFile.read(4))
                    subset.offset, = struct.unpack("<I", meshFile.read(4))
                    subset.bounds.minimum["x"], = struct.unpack("<f", meshFile.read(4))
                    subset.bounds.minimum["y"], = struct.unpack("<f", meshFile.read(4))
                    subset.bounds.minimum["z"], = struct.unpack("<f", meshFile.read(4))
                    subset.bounds.maximum["x"], = struct.unpack("<f", meshFile.read(4))
                    subset.bounds.maximum["y"], = struct.unpack("<f", meshFile.read(4))
                    subset.bounds.maximum["z"], = struct.unpack("<f", meshFile.read(4))
                    nameOffset, = struct.unpack("<I", meshFile.read(4))
                    subset.nameLength, = struct.unpack("<I", meshFile.read(4))
                    if self.meshInfo.fileVersion >= 5:
                        # version 5+
                        subset.lightmapSizeHintWidth, = struct.unpack("<I", meshFile.read(4))
                        subset.lightmapSizeHintHeight, = struct.unpack("<I", meshFile.read(4))
                        subsetByteSize += 48
                    else:
                        subsetByteSize += 40
                    self.subsets.append(subset)
                # adjust for padding after subsets
                offsetTracker.alignedAdvance(subsetByteSize) 
                meshFile.seek(offsetTracker.offset())

                # Subset Names
                for subset in self.subsets:
                    subset.name = meshFile.read(subset.nameLength * 2).decode("utf_16_le")
                    offsetTracker.alignedAdvance(subset.nameLength * 2)
                    meshFile.seek(offsetTracker.offset())

                # Joints
                for jointIndex in range(jointsSize):
                    joint = self.Joint()
                    joint.jointId, = struct.unpack("<I", meshFile.read(4))
                    joint.parentId, = struct.unpack("<I", meshFile.read(4))
                    for x in range(16):
                        joint.invBindPos[x], = struct.unpack("<f", meshFile.read(4))
                    for x in range(16):
                        joint.localToGlobalBoneSpace[x], = struct.unpack("<f", meshFile.read(4))
                    offsetTracker.advance(136)
                    meshFile.seek(offsetTracker.offset())
                    self.joints.append(joint)

                meshFile.close()
        except OSError:
            print("Could not open/read file:", inputFile)
        except: #handle other exceptions such as attribute errors
            print("Unexpected error:", sys.exc_info()[0])
    def writeMesh(self, outputFile, offset):
        try:
            with open(outputFile, "wb") as meshFile:
                # write header placeholder
                meshFile.seek(offset, 0)
                self.meshInfo.fileVersion = 5 # current version is 5
                header,headerSize = self.meshInfo.save()
                meshFile.write(header)
                offsetTracker = self.MeshOffsetTracker(headerSize)
                # write Mesh metadata
                meshMetaData = bytearray()
                meshMetaData += struct.pack("<I", 0)
                meshMetaData += struct.pack("<I", len(self.vertexBuffer.entires))
                meshMetaData += struct.pack("<I", self.vertexBuffer.stride)
                meshMetaData += struct.pack("<I", 0)
                meshMetaData += struct.pack("<I", len(self.vertexBuffer.data))

                meshMetaData += struct.pack("<I", self.indexBuffer.componentType)
                meshMetaData += struct.pack("<I", 0)
                meshMetaData += struct.pack("<I", len(self.indexBuffer.data))

                meshMetaData += struct.pack("<I", 0)
                meshMetaData += struct.pack("<I", len(self.subsets))

                meshMetaData += struct.pack("<I", 0)
                meshMetaData += struct.pack("<I", len(self.joints))

                meshMetaData += struct.pack("<I", self.drawMode)
                meshMetaData += struct.pack("<I", self.winding)

                meshFile.write(meshMetaData)
                offsetTracker.advance(56)

                # Vertex Buffer Entries
                entriesData = bytearray()
                for entry in self.vertexBuffer.entires:
                    entriesData += struct.pack("<I", 0)
                    entriesData += struct.pack("<I", entry.componentType)
                    entriesData += struct.pack("<I", entry.numComponents)
                    entriesData += struct.pack("<I", entry.firstItemOffset)
                entriesData += alignmentHelper(len(entriesData)) # alignment
                offsetTracker.advance(len(entriesData))
                meshFile.write(entriesData)

                # Vertex Buffer Entry Names
                entryNameData = bytearray()
                for entry in self.vertexBuffer.entires:
                    entryNameData += struct.pack("<I", len(entry.name))
                    entryNameData += bytearray(entry.name, 'utf-8')
                    entryNameData += alignmentHelper(len(entry.name))
                meshFile.write(entryNameData)
                offsetTracker.advance(len(entryNameData))

                # write vertex buffer data
                meshFile.write(self.vertexBuffer.data)
                meshFile.write(alignmentHelper(len(self.vertexBuffer.data)))
                offsetTracker.alignedAdvance(len(self.vertexBuffer.data))
                # write index buffer data
                meshFile.write(self.indexBuffer.data)
                meshFile.write(alignmentHelper(len(self.indexBuffer.data)))
                offsetTracker.alignedAdvance(len(self.indexBuffer.data))

                # subsets
                subsetsData = bytearray()
                for subset in self.subsets:
                    subsetsData += struct.pack("<I", subset.count)
                    subsetsData += struct.pack("<I", subset.offset)
                    subsetsData += struct.pack("<f", subset.bounds.minimum["x"])
                    subsetsData += struct.pack("<f", subset.bounds.minimum["y"])
                    subsetsData += struct.pack("<f", subset.bounds.minimum["z"])
                    subsetsData += struct.pack("<f", subset.bounds.maximum["x"])
                    subsetsData += struct.pack("<f", subset.bounds.maximum["y"])
                    subsetsData += struct.pack("<f", subset.bounds.maximum["z"])
                    subsetsData += struct.pack("<I", 0) # offset
                    subsetsData += struct.pack("<I", subset.nameLength)
                    subsetsData += struct.pack("<I", subset.lightmapSizeHintWidth)
                    subsetsData += struct.pack("<I", subset.lightmapSizeHintHeight)
                subsetsData += alignmentHelper(len(subsetsData)) # alignment
                offsetTracker.advance(len(subsetsData))
                meshFile.write(subsetsData)

                # subsets names
                subsetNameData = bytearray()
                for subset in self.subsets:
                    subsetNameData += bytearray(subset.name, 'utf-16le')
                    subsetNameData += alignmentHelper(subset.nameLength * 2)
                meshFile.write(subsetNameData)
                offsetTracker.advance(len(subsetNameData))

                # Now that we know the final size of the mesh, we need to write
                # the header again with the correct size
                meshFile.seek(offset, 0)
                self.meshInfo.fileVersion = 5 # current version is 5
                self.meshInfo.sizeInBytes = offsetTracker.offset() - headerSize
                header,headerSize = self.meshInfo.save()
                meshFile.write(header)

                meshFile.close()
                return offsetTracker.offset()
        except OSError:
            print("Could not open/create file:", outputFile)
        except: #handle other exceptions such as attribute errors
            print("Unexpected error:", sys.exc_info()[0])
    def convertToPointsPrimitive(self):
        print("Converting mesh to Points")
        if self.drawMode != 7:
            print("Conversion not possible with Non-Triangle primitives")
            return False

        # Build new index buffer
        oldIndexes = self.indexBuffer.indexes()
        newIndexes = []
        newOffset = 0
        for subset in self.subsets:
            subsetIndexSet = set()
            for index in range(subset.offset, subset.offset + subset.count):
                subsetIndexSet.add(oldIndexes[index])
            for index in subsetIndexSet:
                newIndexes.append(index)
            subset.offset = newOffset
            subset.count = len(subsetIndexSet)
            newOffset += subset.count

        # Create new index buffer and fill
        componentType = 5 # uint32
        if len(newIndexes) < 65535:
            componentType = 3 # uint16
        self.indexBuffer.setIndexes(newIndexes, componentType)

        self.drawMode = 1 # Points

        return True
    def convertToLinesPrimitive(self):
        print("Converting mesh to Lines")
        if self.drawMode != 7:
            print("Conversion not possible with Non-Triangle primitives")
            return False

        # Build new index buffer
        oldIndexes = self.indexBuffer.indexes()
        newIndexes = []
        newOffset = 0
        for subset in self.subsets:
            index = subset.offset
            subsetIndex = []
            while index + 2 < subset.offset + subset.count:
                vertex1 = oldIndexes[index]
                vertex2 = oldIndexes[index + 1]
                vertex3 = oldIndexes[index + 2]
                subsetIndex.append(vertex1)
                subsetIndex.append(vertex2)
                subsetIndex.append(vertex2)
                subsetIndex.append(vertex3)
                subsetIndex.append(vertex3)
                subsetIndex.append(vertex1)
                index += 3
            subset.offset = newOffset
            subset.count = len(subsetIndex)
            newOffset += subset.count
            for index in subsetIndex:
                newIndexes.append(index)
        
        # Create new index buffer and fill
        componentType = 5 # uint32
        if len(newIndexes) < 65535:
            componentType = 3 # uint16
        self.indexBuffer.setIndexes(newIndexes, componentType)

        self.drawMode = 4 # Lines

        return True

class MultiMeshInfo:
    def __init__(self):
        self.fileId = 555777497
        self.fileVersion = 1
        self.meshEntries = {}

    def loadMultiMeshInfo(self, inputFile):
        try:
            with open(inputFile, "rb") as meshFile:
                # Look for a valid MultiMesh footer
                meshFile.seek(-16, 2) #16 bytes from the end of the file
                self.fileId, = struct.unpack("<I", meshFile.read(4))
                self.fileVersion, = struct.unpack("<I", meshFile.read(4))
                meshFile.seek(4, 1)
                #entriesOffset, = struct.unpack("<I", meshFile.read(4))
                entriesSize, = struct.unpack("<I", meshFile.read(4))

                if self.isValid():
                    # Look for entries
                    for i in range(entriesSize):
                        meshFile.seek(-16 + (-16 * entriesSize) + (16 * i), 2)
                        meshOffset, = struct.unpack("<Q", meshFile.read(8))
                        meshId, = struct.unpack("<I", meshFile.read(4))
                        self.meshEntries[meshId] = meshOffset
                
                meshFile.close()
        except OSError:
            print("Could not open/read file:", inputFile)
        except: #handle other exceptions such as attribute errors
            print("Unexpected error:", sys.exc_info()[0])

    def saveMultiMeshInfo(self, outputFile):
        # This is always appended to the end of the file
        try:
            with open(outputFile, "ab") as meshFile:
                #meshFile.seek(0, 2) # seek end of file
                multiMeshData = bytearray()
                # MeshMultiEntries
                for meshId, meshOffset in self.meshEntries.items():
                    multiMeshData += struct.pack("<Q", meshOffset)
                    multiMeshData += struct.pack("<I", meshId)
                    multiMeshData += struct.pack("<I", 0) # padding
                # MultiMeshFooter
                multiMeshData += struct.pack("<I", self.fileId)
                multiMeshData += struct.pack("<I", self.fileVersion)
                multiMeshData += struct.pack("<I", 0)
                multiMeshData += struct.pack("<I", len(self.meshEntries))
                meshFile.write(multiMeshData)
                meshFile.close()
        except OSError:
            print("Could not open/create file:", outputFile)
        except: #handle other exceptions such as attribute errors
            print("Unexpected error:", sys.exc_info()[0])

    def isValid(self):
        return self.fileId == 555777497 and self.fileVersion == 1

class MeshFile:
    multiMeshInfo = MultiMeshInfo()
    meshes = {}

    def loadMeshFile(self, inputFile):
        self.multiMeshInfo.loadMultiMeshInfo(inputFile);
    
        if self.multiMeshInfo.isValid() and len(self.multiMeshInfo.meshEntries) > 0:
            # This is indeed a MultiMesh file
            for entryId in self.multiMeshInfo.meshEntries.keys():
                offset = self.multiMeshInfo.meshEntries[entryId]
                mesh = Mesh()
                mesh.loadMesh(inputFile, offset)
                self.meshes[entryId] = mesh
        else:
            # This still may be a regular mesh file
            mesh = Mesh()
            mesh.loadMesh(inputFile, 0)
            self.meshes[0] = mesh
    def saveMeshFile(self, outputFile):
        print ('Output file is ', outputFile)

        offset = 0
        multiMeshFooter = MultiMeshInfo()
        for meshIndex, mesh in self.meshes.items():
            multiMeshFooter.meshEntries[meshIndex] = offset
            offset = mesh.writeMesh(outputFile, offset)

        multiMeshFooter.saveMultiMeshInfo(outputFile)

    def convertToPointsPrimitive(self):
        result = False
        for mesh in self.meshes.values():
            result &= mesh.convertToPointsPrimitive()
        return result
    
    def convertToLinesPrimitive(self):
        result = False
        for mesh in self.meshes.values():
            result &= mesh.convertToLinesPrimitive()
        return result