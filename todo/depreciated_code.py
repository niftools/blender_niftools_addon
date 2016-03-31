#__init__.py

'''
    def get_game_to_trans(self, gname):
        symbols = ":,'\" +-*!?;./="
        table = str.maketrans(symbols, "_" * len(symbols))
        enum = gname.upper().translate(table).replace("__", "_")
        return enum

    Fundementally broken versioning system
    def hex_to_dec(self, nif_ver_hex):
        
        nif_ver_hex_1 = str(int('{0:.4}'.format(
                        hex(self.data._version_value_._value)),0)).zfill(2)
        nif_ver_hex_2 = str(int('0x{0:.2}'.format(
                        hex(self.data._version_value_._value)[4:]),0)).zfill(2)
        nif_ver_hex_3 = str(int('0x{0:.2}'.format(
                        hex(self.data._version_value_._value)[6:]),0)).zfill(2)
        nif_ver_hex_4 = str(int('0x{0:.2}'.format(
                        hex(self.data._version_value_._value)[8:]),0)).zfill(2)
        
        nif_ver_dec = str(
        nif_ver_hex_1 + "." + nif_ver_hex_2 + "." + nif_ver_hex_3 + "." + nif_ver_hex_4)
        
        return nif_ver_dec


    def dec_to_hex(self, nif_ver_dec):
        
        dec_split = re.compile(r'\W+')
        dec_split = dec_split.split(nif_ver_dec)

        nif_ver_dec_1, nif_ver_dec_2, nif_ver_dec_3, nif_ver_dec_4 = dec_split
        nif_ver_dec_1 = hex(int(nif_ver_dec_1, 10))[2:].zfill(2)
        nif_ver_dec_2 = hex(int(nif_ver_dec_2, 10))[2:].zfill(2)
        nif_ver_dec_3 = hex(int(nif_ver_dec_3, 10))[2:].zfill(2)
        nif_ver_dec_4 = hex(int(nif_ver_dec_4, 10))[2:].zfill(2)
        nif_ver_hex = int(
            (nif_ver_dec_1 + nif_ver_dec_2 + nif_ver_dec_3 + nif_ver_dec_4), 16)
        return nif_ver_hex

    # version checking to help avoid errors
    # due to invalid settings
    b_scene = bpy.context.scene
    nif_ver_hex = b_scene.niftools.nif_version
    for gname in NifFormat.games:
        gname_trans = self.get_game_to_trans(gname)
        if gname_trans == self.properties.game:
            if nif_ver_hex not in NifFormat.games[gname]:
                raise nif_utils.NifError(
                "Version for export not found: %s"
                % str(nif_ver_hex))
            break

    def import_version_set(self):
        scene = bpy.context.scene
        scene.niftools.nif_version = self.data._version_value_._value
        scene.niftools.user_version = self.data._user_version_value_._value
        scene.niftools.user_version_2 = self.data._user_version_2_value_._value

    self.nif_import.import_version_set(b_col_obj)

    def __init__(self):
        """Initialize and load configuration."""
        # initialize all instance variables
        self.guiElements = {} # dictionary of gui elements (buttons, strings, sliders, ...)
        self.gui_events = []   # list of events
        self.gui_event_ids = {} # dictionary of event ids
        self.config = {}      # configuration dictionary
        self.target = None    # import or export
        self.callback = None  # function to call when config gui is done
        self.texpathIndex = 0
        self.texpathCurrent = ''

        # reset GUI coordinates
        self.xPos = self.XORIGIN
        self.yPos = self.YORIGIN + Blender.Window.GetAreaSize()[1]

        # load configuration
        self.load()

    def run(self, target, filename, callback):
        """Run the config gui."""
        self.target = target     # import or export
        self.callback = callback # function to call when config gui is done

        # save file name
        # (the key where to store the file name depends
        # on the target)
        if self.target == self.TARGET_IMPORT:
            self.config["IMPORT_FILE"] = filename
        elif self.target == self.TARGET_EXPORT:
            self.config["EXPORT_FILE"] = filename
        self.save()

        # prepare and run gui
        self.texpathIndex = 0
        self.update_texpath_current()
        Draw.Register(self.gui_draw, self.gui_event, self.gui_button_event)

    def save(self):
        """Save and validate configuration to Blender registry."""
        Registry.SetKey(self.CONFIG_NAME, self.config, True)
        self.load() # for validation

    def load(self):
        """Load the configuration stored in the Blender registry and checks
        configuration for incompatible values.
        """
        # copy defaults
        self.config = dict(**self.DEFAULTS)
        # read configuration
        savedconfig = Blender.Registry.GetKey(self.CONFIG_NAME, True)
        # port config keys from old versions to current version
        try:
            self.config["IMPORT_TEXTURE_PATH"] = savedconfig["TEXTURE_SEARCH_PATH"]
        except:
            pass
        try:
            self.config["IMPORT_FILE"] = os.path.join(
                savedconfig["NIF_IMPORT_PATH"], savedconfig["NIF_IMPORT_FILE"])
        except:
            pass
        try:
            self.config["EXPORT_FILE"] = savedconfig["NIF_EXPORT_FILE"]
        except:
            pass
        try:
            self.config["IMPORT_REALIGN_BONES"] = savedconfig["REALIGN_BONES"]
        except:
            pass
        try:
            if self.config["IMPORT_REALIGN_BONES"] == True:
                self.config["IMPORT_REALIGN_BONES"] = 1
            elif self.config["IMPORT_REALIGN_BONES"] == False:
                self.config["IMPORT_REALIGN_BONES"] = 0
        except:
            pass
        try:
            if savedconfig["IMPORT_SKELETON"] == True:
                self.config["IMPORT_SKELETON"] = 1
            elif savedconfig["IMPORT_SKELETON"] == False:
                self.config["IMPORT_SKELETON"] = 0
        except:
            pass
        # merge configuration with defaults
        if savedconfig:
            for key, val in self.DEFAULTS.items():
                try:
                    savedval = savedconfig[key]
                except KeyError:
                    pass
                else:
                    if isinstance(savedval, val.__class__):
                        self.config[key] = savedval
        # store configuration
        Blender.Registry.SetKey(self.CONFIG_NAME, self.config, True)
        # special case: set log level here
        self.update_log_level("LOG_LEVEL", self.config["LOG_LEVEL"])

    def event_id(self, event_name):
        """Return event id from event name, and register event if it is new."""
        try:
            event_id = self.gui_event_ids[event_name]
        except KeyError:
            event_id = len(self.gui_events)
            self.gui_event_ids[event_name] = event_id
            self.gui_events.append(event_name)
        if  event_id >= 16383:
            raise RuntimeError("Maximum number of events exceeded")
        return event_id

    def draw_y_sep(self):
        """Vertical skip."""
        self.yPos -= self.YLINESEP

    def draw_next_column(self):
        """Start a new column."""
        self.xPos += self.XCOLUMNSKIP + self.XCOLUMNSEP
        self.yPos = self.YORIGIN + Blender.Window.GetAreaSize()[1]

    def draw_slider(
        self, text, event_name, min_val, max_val, callback, val = None,
        num_items = 1, item = 0):
        """Draw a slider."""
        if val is None:
            val = self.config[event_name]
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.Slider(
            text,
            self.event_id(event_name),
            self.xPos + item*width, self.yPos, width, self.YLINESKIP,
            val, min_val, max_val,
            0, # realtime
            "", # tooltip,
            callback)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def draw_label(self, text, event_name, num_items = 1, item = 0):
        """Draw a line of text."""
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.Label(
            text,
            self.xPos + item*width, self.yPos, width, self.YLINESKIP)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def draw_list(self, text, event_name_prefix, val):
        """Create elements to select a list of things.

        Registers events PREFIX_ITEM, PREFIX_PREV, PREFIX_NEXT, PREFIX_REMOVE
        and PREFIX_ADD."""
        self.guiElements["%s_ITEM"%event_name_prefix]   = Draw.String(
            text,
            self.event_id("%s_ITEM"%event_name_prefix),
            self.xPos, self.yPos, self.XCOLUMNSKIP-90, self.YLINESKIP,
            val, 255)
        self.guiElements["%s_PREV"%event_name_prefix]   = Draw.PushButton(
            '<',
            self.event_id("%s_PREV"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-90, self.yPos, 20, self.YLINESKIP)
        self.guiElements["%s_NEXT"%event_name_prefix]   = Draw.PushButton(
            '>',
            self.event_id("%s_NEXT"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-70, self.yPos, 20, self.YLINESKIP)
        self.guiElements["%s_REMOVE"%event_name_prefix] = Draw.PushButton(
            'X',
            self.event_id("%s_REMOVE"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-50, self.yPos, 20, self.YLINESKIP)
        self.guiElements["%s_ADD"%event_name_prefix]    = Draw.PushButton(
            '...',
            self.event_id("%s_ADD"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-30, self.yPos, 30, self.YLINESKIP)
        self.yPos -= self.YLINESKIP

    def draw_toggle(self, text, event_name, val = None, num_items = 1, item = 0):
        """Draw a toggle button."""
        if val == None:
            val = self.config[event_name]
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.Toggle(
            text,
            self.event_id(event_name),
            self.xPos + item*width, self.yPos, width, self.YLINESKIP,
            val)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def draw_push_button(self, text, event_name, num_items = 1, item = 0):
        """Draw a push button."""
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.PushButton(
            text,
            self.event_id(event_name),
            self.xPos + item*width, self.yPos, width, self.YLINESKIP)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def draw_number(
        self, text, event_name, min_val, max_val, callback, val = None,
        num_items = 1, item = 0):
        """Draw an input widget for numbers."""
        if val is None:
            val = self.config[event_name]
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.Number(
            text,
            self.event_id(event_name),
            self.xPos + item*width, self.yPos, width, self.YLINESKIP,
            val,
            min_val, max_val,
            "", # tooltip
            callback)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def draw_file_browse(self, text, event_name_prefix, val = None):
        """Create elements to select a file.

        Registers events PREFIX_ITEM, PREFIX_REMOVE, PREFIX_ADD."""
        if val is None:
            val = self.config[event_name_prefix]
        self.guiElements["%s_ITEM"%event_name_prefix]   = Draw.String(
            text,
            self.event_id("%s_ITEM"%event_name_prefix),
            self.xPos, self.yPos, self.XCOLUMNSKIP-50, self.YLINESKIP,
            val, 255)
        self.guiElements["%s_REMOVE"%event_name_prefix] = Draw.PushButton(
            'X',
            self.event_id("%s_REMOVE"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-50, self.yPos, 20, self.YLINESKIP)
        self.guiElements["%s_ADD"%event_name_prefix]    = Draw.PushButton(
            '...',
            self.event_id("%s_ADD"%event_name_prefix),
            self.xPos+self.XCOLUMNSKIP-30, self.yPos, 30, self.YLINESKIP)
        self.yPos -= self.YLINESKIP

    def draw_string(self, text, event_name, max_length, callback, val = None,
                   num_items = 1, item = 0):
        """Create elements to input a string."""
        if val is None:
            val = self.config[event_name]
        width = self.XCOLUMNSKIP//num_items
        self.guiElements[event_name] = Draw.String(
            text,
            self.event_id(event_name),
            self.xPos + item*width, self.yPos, width, self.YLINESKIP,
            val,
            max_length,
            "", # tooltip
            callback)
        if item + 1 == num_items:
            self.yPos -= self.YLINESKIP

    def gui_draw(self):
        """Draw config GUI."""
        # reset position
        self.xPos = self.XORIGIN
        self.yPos = self.YORIGIN + Blender.Window.GetAreaSize()[1]

        # common options
        self.draw_label(
            text = self.WELCOME_MESSAGE,
            event_name = "LABEL_WELCOME_MESSAGE")
        self.draw_y_sep()

        self.draw_number(
            text = "Log Level",
            event_name = "LOG_LEVEL",
            min_val = 0, max_val = 99,
            callback = self.update_log_level,
            num_items = 4, item = 0)
        self.draw_push_button(
            text = "Warn",
            event_name = "LOG_LEVEL_WARN",
            num_items = 4, item = 1)
        self.draw_push_button(
            text = "Info",
            event_name = "LOG_LEVEL_INFO",
            num_items = 4, item = 2)
        self.draw_push_button(
            text = "Debug",
            event_name = "LOG_LEVEL_DEBUG",
            num_items = 4, item = 3)
        self.draw_y_sep()

        self.draw_slider(
            text = "Scale Correction:  ",
            event_name = "SCALE_CORRECTION",
            val = self.config["EXPORT_SCALE_CORRECTION"],
            min_val = 0.01, max_val = 100.0,
            callback = self.update_scale)
        self.draw_y_sep()

        # import-only options
        if self.target == self.TARGET_IMPORT:
            self.draw_label(
                text = "Texture Search Paths:",
                event_name = "TEXPATH_TEXT")
            self.draw_list(
                text = "",
                event_name_prefix = "TEXPATH",
                val = self.texpathCurrent)
            self.draw_y_sep()

            self.draw_toggle(
                text = "Import Animation",
                event_name = "IMPORT_ANIMATION")
            self.draw_y_sep()

            self.draw_toggle(
                text = "Import Extra Nodes",
                event_name = "IMPORT_EXTRANODES")
            self.draw_y_sep()
            
            self.draw_toggle(
                text = "Import Skeleton Only + Parent Selected",
                event_name = "IMPORT_SKELETON_1",
                val = (self.config["IMPORT_SKELETON"] == 1))
            self.draw_toggle(
                text = "Import Geometry Only + Parent To Selected Armature",
                event_name = "IMPORT_SKELETON_2",
                val = (self.config["IMPORT_SKELETON"] == 2))
            self.draw_y_sep()

            self.draw_toggle(
                text = "Save Embedded Textures As DDS",
                event_name = "IMPORT_EXPORTEMBEDDEDTEXTURES")
            self.draw_y_sep()

            self.draw_toggle(
                text = "Combine NiNode + Shapes Into Single Mesh",
                event_name = "IMPORT_COMBINESHAPES")
            self.draw_y_sep()

            self.draw_label(
                text = "Keyframe File:",
                event_name = "IMPORT_KEYFRAMEFILE_TEXT")
            self.draw_file_browse(
                text = "",
                event_name_prefix = "IMPORT_KEYFRAMEFILE")
            self.draw_y_sep()

            self.draw_label(
                text = "FaceGen EGM File:",
                event_name = "IMPORT_EGMFILE_TEXT")
            self.draw_file_browse(
                text = "",
                event_name_prefix = "IMPORT_EGMFILE")
            self.draw_toggle(
                text="Animate",
                event_name="IMPORT_EGMANIM",
                num_items=2, item=0)
            self.draw_slider(
                text="Scale:  ",
                event_name="IMPORT_EGMANIMSCALE",
                val=self.config["IMPORT_EGMANIMSCALE"],
                min_val=0.01, max_val=100.0,
                callback=self.update_egm_anim_scale,
                num_items=2, item=1)
            self.draw_y_sep()

            self.draw_push_button(
                text = "Restore Default Settings",
                event_name = "IMPORT_SETTINGS_DEFAULT")
            self.draw_y_sep()

            self.draw_label(
                text = "... and if skinning fails with default settings:",
                event_name = "IMPORT_SETTINGS_SKINNING_TEXT")
            self.draw_push_button(
                text = "Use The Force Luke",
                event_name = "IMPORT_SETTINGS_SKINNING")
            self.draw_y_sep()

        # export-only options
        if self.target == self.TARGET_EXPORT:

            self.draw_string(
                text = "Anim Seq Name: ",
                event_name = "EXPORT_ANIMSEQUENCENAME",
                max_length = 128,
                callback = self.update_anim_sequence_name)
            self.draw_string(
                text = "Anim Target Name: ",
                event_name = "EXPORT_ANIMTARGETNAME",
                max_length = 128,
                callback = self.update_anim_target_name)
            self.draw_number(
                text = "Bone Priority: ",
                event_name = "EXPORT_ANIMPRIORITY",
                min_val = 0, max_val = 100,
                callback = self.update_anim_priority,
                num_items = 2, item = 0)
            self.draw_toggle(
                text = "Ignore Blender Anim Props",
                event_name = "EXPORT_ANIM_DO_NOT_USE_BLENDER_PROPERTIES",
                num_items = 2, item = 1)  
            self.draw_y_sep()

            self.draw_toggle(
                text = "Combine Materials to Increase Performance",
                event_name = "EXPORT_OPTIMIZE_MATERIALS")
            self.draw_y_sep()

        self.draw_push_button(
            text = "Ok",
            event_name = "OK",
            num_items = 3, item = 0)
        # (item 1 is whitespace)
        self.draw_push_button(
            text = "Cancel",
            event_name = "CANCEL",
            num_items = 3, item = 2)

        # advanced import settings
        if self.target == self.TARGET_IMPORT:
            self.draw_next_column()

            self.draw_toggle(
                text = "Realign Bone Tail Only",
                event_name = "IMPORT_REALIGN_BONES_1",
                val = (self.config["IMPORT_REALIGN_BONES"] == 1),
                num_items = 2, item = 0)
            self.draw_toggle(
                text = "Realign Bone Tail + Roll",
                event_name = "IMPORT_REALIGN_BONES_2",
                val = (self.config["IMPORT_REALIGN_BONES"] == 2),
                num_items = 2, item = 1)
            self.draw_toggle(
                text="Merge Skeleton Roots",
                event_name="IMPORT_MERGESKELETONROOTS")
            self.draw_toggle(
                text="Send Geometries To Bind Position",
                event_name="IMPORT_SENDGEOMETRIESTOBINDPOS")
            self.draw_toggle(
                text="Send Detached Geometries To Node Position",
                event_name="IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS")
            self.draw_toggle(
                text="Send Bones To Bind Position",
                event_name="IMPORT_SENDBONESTOBINDPOS")
            self.draw_toggle(
                text = "Apply Skin Deformation",
                event_name = "IMPORT_APPLYSKINDEFORM")
            self.draw_y_sep()

        # export-only options for oblivion/fallout 3

        if (self.target == self.TARGET_EXPORT
            and self.config["game"] in ('OBLIVION', 'FALLOUT_3')):
            self.draw_next_column()
            
            self.draw_label(
                text = "Collision Options",
                event_name = "EXPORT_OB_COLLISIONHTML")
            self.draw_push_button(
                text = "Static",
                event_name = "EXPORT_OB_RIGIDBODY_STATIC",
                num_items = 5, item = 0)
            self.draw_push_button(
                text = "Anim Static",
                event_name = "EXPORT_OB_RIGIDBODY_ANIMATED",
                num_items = 5, item = 1)
            self.draw_push_button(
                text = "Clutter",
                event_name = "EXPORT_OB_RIGIDBODY_CLUTTER",
                num_items = 5, item = 2)
            self.draw_push_button(
                text = "Weapon",
                event_name = "EXPORT_OB_RIGIDBODY_WEAPON",
                num_items = 5, item = 3)
            self.draw_push_button(
                text = "Creature",
                event_name = "EXPORT_OB_RIGIDBODY_CREATURE",
                num_items = 5, item = 4)
            self.draw_toggle(
                text = "Stone",
                event_name = "EXPORT_OB_MATERIAL_STONE",
                val = self.config["EXPORT_OB_MATERIAL"] == 0,
                num_items = 6, item = 0)
            self.draw_toggle(
                text = "Cloth",
                event_name = "EXPORT_OB_MATERIAL_CLOTH",
                val = self.config["EXPORT_OB_MATERIAL"] == 1,
                num_items = 6, item = 1)
            self.draw_toggle(
                text = "Glass",
                event_name = "EXPORT_OB_MATERIAL_GLASS",
                val = self.config["EXPORT_OB_MATERIAL"] == 3,
                num_items = 6, item = 2)
            self.draw_toggle(
                text = "Metal",
                event_name = "EXPORT_OB_MATERIAL_METAL",
                val = self.config["EXPORT_OB_MATERIAL"] == 5,
                num_items = 6, item = 3)
            self.draw_toggle(
                text = "Skin",
                event_name = "EXPORT_OB_MATERIAL_SKIN",
                val = self.config["EXPORT_OB_MATERIAL"] == 7,
                num_items = 6, item = 4)
            self.draw_toggle(
                text = "Wood",
                event_name = "EXPORT_OB_MATERIAL_WOOD",
                val = self.config["EXPORT_OB_MATERIAL"] == 9,
                num_items = 6, item = 5)
            self.draw_number(
                text = "Material:  ",
                event_name = "EXPORT_OB_MATERIAL",
                min_val = 0, max_val = 30,
                callback = self.update_ob_material)
            self.draw_number(
                text = "BSX Flags:  ",
                event_name = "EXPORT_OB_BSXFLAGS",
                min_val = 0, max_val = 63,
                callback = self.update_ob_bsx_flags,
                num_items = 2, item = 0)
            self.draw_slider(
                text = "Mass:  ",
                event_name = "EXPORT_OB_MASS",
                min_val = 0.1, max_val = 1500.0,
                callback = self.update_ob_mass,
                num_items = 2, item = 1)
            self.draw_number(
                text = "Layer:  ",
                event_name = "EXPORT_OB_LAYER",
                min_val = 0, max_val = 57,
                callback = self.update_ob_layer,
                num_items = 3, item = 0)
            self.draw_number(
                text = "Motion System:  ",
                event_name = "EXPORT_OB_MOTIONSYSTEM",
                min_val = 0, max_val = 9,
                callback = self.update_ob_motion_system,
                num_items = 3, item = 1)
            self.draw_number(
                text = "Quality Type:  ",
                event_name = "EXPORT_OB_QUALITYTYPE",
                min_val = 0, max_val = 8,
                callback = self.update_ob_quality_type,
                num_items = 3, item = 2)
            self.draw_number(
                text = "Unk Byte 1:  ",
                event_name = "EXPORT_OB_UNKNOWNBYTE1",
                min_val = 1, max_val = 2,
                callback = self.update_ob_unknown_byte_1,
                num_items = 3, item = 0)
            self.draw_number(
                text = "Unk Byte 2:  ",
                event_name = "EXPORT_OB_UNKNOWNBYTE2",
                min_val = 1, max_val = 2,
                callback = self.update_ob_unknown_byte_2,
                num_items = 3, item = 1)
            self.draw_number(
                text = "Wind:  ",
                event_name = "EXPORT_OB_WIND",
                min_val = 0, max_val = 1,
                callback = self.update_ob_wind,
                num_items = 3, item = 2)
            self.draw_toggle(
                text = "Solid",
                event_name = "EXPORT_OB_SOLID",
                num_items = 2, item = 0)
            self.draw_toggle(
                text = "Hollow",
                event_name = "EXPORT_OB_HOLLOW",
                val = not self.config["EXPORT_OB_SOLID"],
                num_items = 2, item = 1)
            self.draw_y_sep()

            self.draw_toggle(
                text = "Use bhkListShape",
                event_name = "EXPORT_BHKLISTSHAPE",
                num_items = 2, item = 0)
            self.draw_toggle(
                text = "Use bhkMalleableConstraint",
                event_name = "EXPORT_OB_MALLEABLECONSTRAINT",
                num_items = 2, item = 1)
            self.draw_toggle(
                text = "Do Not Use Blender Collision Properties",
                event_name = "EXPORT_OB_COLLISION_DO_NOT_USE_BLENDER_PROPERTIES")   
            self.draw_y_sep()

            self.draw_label(
                text = "Weapon Body Location",
                event_name = "LABEL_WEAPON_LOCATION")
            self.draw_toggle(
                text = "None",
                val = self.config["EXPORT_OB_PRN"] == "NONE",
                event_name = "EXPORT_OB_PRN_NONE",
                num_items = 7, item = 0)
            self.draw_toggle(
                text = "Back",
                val = self.config["EXPORT_OB_PRN"] == "BACK",
                event_name = "EXPORT_OB_PRN_BACK",
                num_items = 7, item = 1)
            self.draw_toggle(
                text = "Side",
                val = self.config["EXPORT_OB_PRN"] == "SIDE",
                event_name = "EXPORT_OB_PRN_SIDE",
                num_items = 7, item = 2)
            self.draw_toggle(
                text = "Quiver",
                val = self.config["EXPORT_OB_PRN"] == "QUIVER",
                event_name = "EXPORT_OB_PRN_QUIVER",
                num_items = 7, item = 3)
            self.draw_toggle(
                text = "Shield",
                val = self.config["EXPORT_OB_PRN"] == "SHIELD",
                event_name = "EXPORT_OB_PRN_SHIELD",
                num_items = 7, item = 4)
            self.draw_toggle(
                text = "Helm",
                val = self.config["EXPORT_OB_PRN"] == "HELM",
                event_name = "EXPORT_OB_PRN_HELM",
                num_items = 7, item = 5)
            self.draw_toggle(
                text = "Ring",
                val = self.config["EXPORT_OB_PRN"] == "RING",
                event_name = "EXPORT_OB_PRN_RING",
                num_items = 7, item = 6)
            self.draw_y_sep()

        # export-only options for fallout 3
        if (self.target == self.TARGET_EXPORT
            and self.config["game"] == 'FALLOUT_3'):
            self.draw_next_column()

            self.draw_label(
                text = "Shader Options",
                event_name = "LABEL_FO3_SHADER_OPTIONS")
            self.draw_push_button(
                text = "Default",
                event_name = "EXPORT_FO3_SHADER_OPTION_DEFAULT",
                num_items = 3, item = 0)
            self.draw_push_button(
                text = "Skin",
                event_name = "EXPORT_FO3_SHADER_OPTION_SKIN",
                num_items = 3, item = 1)
            self.draw_push_button(
                text = "Cloth",
                event_name = "EXPORT_FO3_SHADER_OPTION_CLOTH",
                num_items = 3, item = 2)
            self.draw_toggle(
                text = "Default Type",
                val = self.config["EXPORT_FO3_SHADER_TYPE"] == 1,
                event_name = "EXPORT_FO3_SHADER_TYPE_DEFAULT",
                num_items = 2, item = 0)
            self.draw_toggle(
                text = "Skin Type",
                val = self.config["EXPORT_FO3_SHADER_TYPE"] == 14,
                event_name = "EXPORT_FO3_SHADER_TYPE_SKIN",
                num_items = 2, item = 1)
            self.draw_toggle(
                text = "Z Buffer",
                event_name = "EXPORT_FO3_SF_ZBUF",
                num_items = 3, item = 0)
            self.draw_toggle(
                text = "Shadow Map",
                event_name = "EXPORT_FO3_SF_SMAP",
                num_items = 3, item = 1)
            self.draw_toggle(
                text = "Shadow Frustum",
                event_name = "EXPORT_FO3_SF_SFRU",
                num_items = 3, item = 2)
            self.draw_toggle(
                text = "Window Envmap",
                event_name = "EXPORT_FO3_SF_WINDOW_ENVMAP",
                num_items = 3, item = 0)
            self.draw_toggle(
                text = "Empty",
                event_name = "EXPORT_FO3_SF_EMPT",
                num_items = 3, item = 1)
            self.draw_toggle(
                text = "Unknown 31",
                event_name = "EXPORT_FO3_SF_UN31",
                num_items = 3, item = 2)
            self.draw_y_sep()

            self.draw_toggle(
                text = "Use BSFadeNode Root",
                event_name = "EXPORT_FO3_FADENODE")
            self.draw_y_sep()

            self.draw_toggle(
                text = "Export Dismember Body Parts",
                event_name = "EXPORT_FO3_BODYPARTS")
            self.draw_y_sep()

        # is this needed?
        #Draw.Redraw(1)

    def gui_button_event(self, evt):
        """Event handler for buttons."""
        try:
            evName = self.gui_events[evt]
        except IndexError:
            evName = None

        if evName == "OK":
            self.save()
            self.gui_exit()
        elif evName == "CANCEL":
            self.callback = None
            self.gui_exit()
        elif evName == "TEXPATH_ADD":
            # browse and add texture search path
            Blender.Window.FileSelector(self.add_texture_path, "Add Texture Search Path")
        elif evName == "TEXPATH_NEXT":
            if self.texpathIndex < (len(self.config["IMPORT_TEXTURE_PATH"])-1):
                self.texpathIndex += 1
            self.update_texpath_current()
        elif evName == "TEXPATH_PREV":
            if self.texpathIndex > 0:
                self.texpathIndex -= 1
            self.update_texpath_current()
        elif evName == "TEXPATH_REMOVE":
            if self.texpathIndex < len(self.config["IMPORT_TEXTURE_PATH"]):
                del self.config["IMPORT_TEXTURE_PATH"][self.texpathIndex]
            if self.texpathIndex > 0:
                self.texpathIndex -= 1
            self.update_texpath_current()

        elif evName == "IMPORT_KEYFRAMEFILE_ADD":
            kffile = self.config["IMPORT_KEYFRAMEFILE"]
            if not kffile:
                kffile = os.path.dirname(self.config["IMPORT_FILE"])
            # browse and add keyframe file
            Blender.Window.FileSelector(
                self.select_keyframe_file, "Select Keyframe File", kffile)
            self.config["IMPORT_ANIMATION"] = True
        elif evName == "IMPORT_KEYFRAMEFILE_REMOVE":
            self.config["IMPORT_KEYFRAMEFILE"] = ''
            self.config["IMPORT_ANIMATION"] = False

        elif evName == "IMPORT_EGMFILE_ADD":
            egmfile = self.config["IMPORT_EGMFILE"]
            if not egmfile:
                egmfile = self.config["IMPORT_FILE"][:-3] + "egm"
            # browse and add egm file
            Blender.Window.FileSelector(
                self.select_egm_file, "Select FaceGen EGM File", egmfile)
        elif evName == "IMPORT_EGMFILE_REMOVE":
            self.config["IMPORT_EGMFILE"] = ''

        elif evName == "IMPORT_REALIGN_BONES_1":
            if self.config["IMPORT_REALIGN_BONES"] == 1:
                self.config["IMPORT_REALIGN_BONES"] = 0
            else:
                self.config["IMPORT_REALIGN_BONES"] = 1
        elif evName == "IMPORT_REALIGN_BONES_2":
            if self.config["IMPORT_REALIGN_BONES"] == 2:
                self.config["IMPORT_REALIGN_BONES"] = 0
            else:
                self.config["IMPORT_REALIGN_BONES"] = 2
        elif evName == "IMPORT_ANIMATION":
            self.config["IMPORT_ANIMATION"] = not self.config["IMPORT_ANIMATION"]
        elif evName == "IMPORT_SKELETON_1":
            if self.config["IMPORT_SKELETON"] == 1:
                self.config["IMPORT_SKELETON"] = 0
            else:
                self.config["IMPORT_SKELETON"] = 1
        elif evName == "IMPORT_SKELETON_2":
            if self.config["IMPORT_SKELETON"] == 2:
                self.config["IMPORT_SKELETON"] = 0
            else:
                self.config["IMPORT_SKELETON"] = 2
        elif evName == "IMPORT_MERGESKELETONROOTS":
            self.config["IMPORT_MERGESKELETONROOTS"] = not self.config["IMPORT_MERGESKELETONROOTS"]
        elif evName == "IMPORT_SENDGEOMETRIESTOBINDPOS":
            self.config["IMPORT_SENDGEOMETRIESTOBINDPOS"] = not self.config["IMPORT_SENDGEOMETRIESTOBINDPOS"]
        elif evName == "IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS":
            self.config["IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS"] = not self.config["IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS"]
        elif evName == "IMPORT_SENDBONESTOBINDPOS":
            self.config["IMPORT_SENDBONESTOBINDPOS"] = not self.config["IMPORT_SENDBONESTOBINDPOS"]
        elif evName == "IMPORT_APPLYSKINDEFORM":
            self.config["IMPORT_APPLYSKINDEFORM"] = not self.config["IMPORT_APPLYSKINDEFORM"]
        elif evName == "IMPORT_EXTRANODES":
            self.config["IMPORT_EXTRANODES"] = not self.config["IMPORT_EXTRANODES"]
        elif evName == "IMPORT_EXPORTEMBEDDEDTEXTURES":
            self.config["IMPORT_EXPORTEMBEDDEDTEXTURES"] = not self.config["IMPORT_EXPORTEMBEDDEDTEXTURES"]
        elif evName == "IMPORT_COMBINESHAPES":
            self.config["IMPORT_COMBINESHAPES"] = not self.config["IMPORT_COMBINESHAPES"]
        elif evName == "IMPORT_EGMANIM":
            self.config["IMPORT_EGMANIM"] = not self.config["IMPORT_EGMANIM"]
        elif evName == "IMPORT_SETTINGS_DEFAULT":
            self.config["IMPORT_ANIMATION"] = True
            self.config["IMPORT_SKELETON"] = 0
            self.config["IMPORT_EXPORTEMBEDDEDTEXTURES"] = False
            self.config["IMPORT_COMBINESHAPES"] = True
            self.config["IMPORT_REALIGN_BONES"] = 1
            self.config["IMPORT_MERGESKELETONROOTS"] = True
            self.config["IMPORT_SENDGEOMETRIESTOBINDPOS"] = True
            self.config["IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS"] = True
            self.config["IMPORT_SENDBONESTOBINDPOS"] = True
            self.config["IMPORT_APPLYSKINDEFORM"] = False
            self.config["IMPORT_EXTRANODES"] = True
            self.config["IMPORT_EGMFILE"] = ''
            self.config["IMPORT_EGMANIM"] = True
            self.config["IMPORT_EGMANIMSCALE"] = 1.0
        elif evName == "IMPORT_SETTINGS_SKINNING":
            self.config["IMPORT_ANIMATION"] = True
            self.config["IMPORT_SKELETON"] = 0
            self.config["IMPORT_EXPORTEMBEDDEDTEXTURES"] = False
            self.config["IMPORT_COMBINESHAPES"] = True
            self.config["IMPORT_REALIGN_BONES"] = 1
            self.config["IMPORT_MERGESKELETONROOTS"] = True
            self.config["IMPORT_SENDGEOMETRIESTOBINDPOS"] = False
            self.config["IMPORT_SENDDETACHEDGEOMETRIESTONODEPOS"] = False
            self.config["IMPORT_SENDBONESTOBINDPOS"] = False
            self.config["IMPORT_APPLYSKINDEFORM"] = True
            self.config["IMPORT_EXTRANODES"] = True
        elif evName[:5] == "GAME_":
            self.config["game"] = evName[5:]
            # settings that usually make sense, fail-safe
            self.config["EXPORT_SMOOTHOBJECTSEAMS"] = True
            self.config["EXPORT_STRIPIFY"] = False
            self.config["EXPORT_STITCHSTRIPS"] = False
            self.config["EXPORT_ANIMATION"] = 1
            self.config["EXPORT_FLATTENSKIN"] = False
            self.config["EXPORT_SKINPARTITION"] = False
            self.config["EXPORT_BONESPERPARTITION"] = 4
            self.config["EXPORT_PADBONES"] = False
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_MW_NIFXNIFKF"] = False
            self.config["EXPORT_MW_BS_ANIMATION_NODE"] = False
            # set default settings per game
            if self.config["game"] == 'FREEDOM_FORCE_VS_THE_3RD_REICH':
                self.config["EXPORT_SKINPARTITION"] = True
                self.config["EXPORT_PADBONES"] = True
            elif self.config["game"] == "Civilization IV":
                self.config["EXPORT_STRIPIFY"] = True
                self.config["EXPORT_STITCHSTRIPS"] = True
                self.config["EXPORT_BONESPERPARTITION"] = 18
                self.config["EXPORT_SKINPARTITION"] = True
            elif self.config["game"] in ('OBLIVION', 'FALLOUT_3'):
                self.config["EXPORT_STRIPIFY"] = True
                self.config["EXPORT_STITCHSTRIPS"] = True
                self.config["EXPORT_FLATTENSKIN"] = True
                self.config["EXPORT_BONESPERPARTITION"] = 18
                self.config["EXPORT_SKINPARTITION"] = True
                # oblivion specific settings
                self.config["EXPORT_BHKLISTSHAPE"] = False
                self.config["EXPORT_OB_MATERIAL"] = 9 # wood
                self.config["EXPORT_OB_MALLEABLECONSTRAINT"] = False
                # rigid body: static
                self.config["EXPORT_OB_BSXFLAGS"] = 2
                self.config["EXPORT_OB_MASS"] = 1000.0
                self.config["EXPORT_OB_MOTIONSYSTEM"] = 7 # MO_SYS_FIXED
                self.config["EXPORT_OB_UNKNOWNBYTE1"] = 1
                self.config["EXPORT_OB_UNKNOWNBYTE2"] = 1
                self.config["EXPORT_OB_QUALITYTYPE"] = 1 # MO_QUAL_FIXED
                self.config["EXPORT_OB_WIND"] = 0
                self.config["EXPORT_OB_LAYER"] = 1 # static
                # shader options
                self.config["EXPORT_FO3_SHADER_TYPE"] = 1
                self.config["EXPORT_FO3_SF_ZBUF"] = True
                self.config["EXPORT_FO3_SF_SMAP"] = False
                self.config["EXPORT_FO3_SF_SFRU"] = False
                self.config["EXPORT_FO3_SF_WINDOW_ENVMAP"] = False
                self.config["EXPORT_FO3_SF_EMPT"] = True
                self.config["EXPORT_FO3_SF_UN31"] = True
                # body parts
                self.config["EXPORT_FO3_BODYPARTS"] = True
            elif self.config["game"] == "Empire Earth II":
                self.config["EXPORT_SKINPARTITION"] = False
            elif self.config["game"] == "Bully SE":
                self.config["EXPORT_STRIPIFY"] = False
                self.config["EXPORT_STITCHSTRIPS"] = False
                self.config["EXPORT_FLATTENSKIN"] = False
                self.config["EXPORT_SKINPARTITION"] = True
                self.config["EXPORT_PADBONES"] = True
                self.config["EXPORT_BONESPERPARTITION"] = 4
        elif evName[:8] == "VERSION_":
            self.config["game"] = evName[8:]
        elif evName == "EXPORT_FLATTENSKIN":
            self.config["EXPORT_FLATTENSKIN"] = not self.config["EXPORT_FLATTENSKIN"]
            if self.config["EXPORT_FLATTENSKIN"]: # if skin is flattened
                self.config["EXPORT_ANIMATION"] = 1 # force geometry only
        elif evName == "EXPORT_STRIPIFY":
            self.config["EXPORT_STRIPIFY"] = not self.config["EXPORT_STRIPIFY"]
        elif evName == "EXPORT_STITCHSTRIPS":
            self.config["EXPORT_STITCHSTRIPS"] = not self.config["EXPORT_STITCHSTRIPS"]
        elif evName == "EXPORT_SMOOTHOBJECTSEAMS":
            self.config["EXPORT_SMOOTHOBJECTSEAMS"] = not self.config["EXPORT_SMOOTHOBJECTSEAMS"]
        elif evName[:17] == "EXPORT_ANIMATION_":
            value = int(evName[17:])
            self.config["EXPORT_ANIMATION"] = value
            if value == 0 or value == 2: # if animation is exported
                self.config["EXPORT_FLATTENSKIN"] = False # disable flattening skin
            elif value == 1:
                # enable flattening skin for 'geometry only' exports
                # in oblivion and fallout 3
                if self.config["game"] in ('OBLIVION', 'FALLOUT_3'):
                    self.config["EXPORT_FLATTENSKIN"] = True
        elif evName == "EXPORT_SKINPARTITION":
            self.config["EXPORT_SKINPARTITION"] = not self.config["EXPORT_SKINPARTITION"]
        elif evName == "EXPORT_PADBONES":
            self.config["EXPORT_PADBONES"] = not self.config["EXPORT_PADBONES"]
            if self.config["EXPORT_PADBONES"]: # bones are padded
                self.config["EXPORT_BONESPERPARTITION"] = 4 # force 4 bones per partition
        elif evName == "EXPORT_BHKLISTSHAPE":
            self.config["EXPORT_BHKLISTSHAPE"] = not self.config["EXPORT_BHKLISTSHAPE"]
        elif evName == "EXPORT_OB_MALLEABLECONSTRAINT":
            self.config["EXPORT_OB_MALLEABLECONSTRAINT"] = not self.config["EXPORT_OB_MALLEABLECONSTRAINT"]
        elif evName == "EXPORT_OB_COLLISION_DO_NOT_USE_BLENDER_PROPERTIES":
            self.config["EXPORT_OB_COLLISION_DO_NOT_USE_BLENDER_PROPERTIES"] = not self.config["EXPORT_OB_COLLISION_DO_NOT_USE_BLENDER_PROPERTIES"]
        elif evName == "EXPORT_OB_SOLID":
            self.config["EXPORT_OB_SOLID"] = True
        elif evName == "EXPORT_OB_HOLLOW":
            self.config["EXPORT_OB_SOLID"] = False
        elif evName == "EXPORT_OB_RIGIDBODY_STATIC":
            self.config["EXPORT_OB_MATERIAL"] = 0 # stone
            self.config["EXPORT_OB_BSXFLAGS"] = 2 # havok
            self.config["EXPORT_OB_MASS"] = 10.0
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 7 # MO_SYS_FIXED
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 1
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 1
            self.config["EXPORT_OB_QUALITYTYPE"] = 1 # MO_QUAL_FIXED
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 1 # static
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_OB_PRN"] = "NONE"
        elif evName == "EXPORT_OB_RIGIDBODY_ANIMATED": # see fencedoor01.nif
            self.config["EXPORT_OB_MATERIAL"] = 0 # stone
            self.config["EXPORT_OB_BSXFLAGS"] = 11 # havok + anim + unknown
            self.config["EXPORT_OB_MASS"] = 10.0
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 6 # MO_SYS_KEYFRAMED
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 2
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 2
            self.config["EXPORT_OB_QUALITYTYPE"] = 2 # MO_QUAL_KEYFRAMED
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 2 # OL_ANIM_STATIC
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_OB_PRN"] = "NONE"
        elif evName == "EXPORT_OB_RIGIDBODY_CLUTTER":
            self.config["EXPORT_OB_BSXFLAGS"] = 3 # anim + havok
            self.config["EXPORT_OB_MASS"] = 10.0 # typical
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 4 # MO_SYS_BOX
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 2
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 2
            self.config["EXPORT_OB_QUALITYTYPE"] = 3 # MO_QUAL_DEBRIS
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 4 # clutter
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_OB_PRN"] = "NONE"
        elif evName == "EXPORT_OB_RIGIDBODY_WEAPON":
            self.config["EXPORT_OB_MATERIAL"] = 5 # metal
            self.config["EXPORT_OB_BSXFLAGS"] = 3 # anim + havok
            self.config["EXPORT_OB_MASS"] = 25.0 # typical
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 4 # MO_SYS_BOX
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 2
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 2
            self.config["EXPORT_OB_QUALITYTYPE"] = 3 # MO_QUAL_DEBRIS
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 5 # weapin
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_OB_PRN"] = "SIDE"
        elif evName == "EXPORT_OB_RIGIDBODY_CREATURE":
            self.config["EXPORT_OB_MATERIAL"] = 7 # skin
            self.config["EXPORT_OB_BSXFLAGS"] = 7 # anim + havok + skeleton
            self.config["EXPORT_OB_MASS"] = 600.0 # single person's weight in Oblivion
            self.config["EXPORT_OB_MOTIONSYSTEM"] = 6 # MO_SYS_KEYFRAMED
            self.config["EXPORT_OB_UNKNOWNBYTE1"] = 2
            self.config["EXPORT_OB_UNKNOWNBYTE2"] = 2
            self.config["EXPORT_OB_QUALITYTYPE"] = 2 # MO_QUAL_KEYFRAMED
            self.config["EXPORT_OB_WIND"] = 0
            self.config["EXPORT_OB_LAYER"] = 8 # biped
            self.config["EXPORT_OB_SOLID"] = True
            self.config["EXPORT_OB_PRN"] = "NONE"
        elif evName == "EXPORT_OB_MATERIAL_STONE":
            self.config["EXPORT_OB_MATERIAL"] = 0
        elif evName == "EXPORT_OB_MATERIAL_CLOTH":
            self.config["EXPORT_OB_MATERIAL"] = 1
        elif evName == "EXPORT_OB_MATERIAL_GLASS":
            self.config["EXPORT_OB_MATERIAL"] = 3
        elif evName == "EXPORT_OB_MATERIAL_METAL":
            self.config["EXPORT_OB_MATERIAL"] = 5
        elif evName == "EXPORT_OB_MATERIAL_SKIN":
            self.config["EXPORT_OB_MATERIAL"] = 7
        elif evName == "EXPORT_OB_MATERIAL_WOOD":
            self.config["EXPORT_OB_MATERIAL"] = 9
        elif evName[:14] == "EXPORT_OB_PRN_":
            self.config["EXPORT_OB_PRN"] = evName[14:]
        elif evName == "EXPORT_OPTIMIZE_MATERIALS":
            self.config["EXPORT_OPTIMIZE_MATERIALS"] = not self.config["EXPORT_OPTIMIZE_MATERIALS"]
        elif evName == "LOG_LEVEL_WARN":
            self.update_log_level(evName, logging.WARNING)
        elif evName == "LOG_LEVEL_INFO":
            self.update_log_level(evName, logging.INFO)
        elif evName == "LOG_LEVEL_DEBUG":
            self.update_log_level(evName, logging.DEBUG)
        elif evName == "EXPORT_FO3_FADENODE":
            self.config["EXPORT_FO3_FADENODE"] = not self.config["EXPORT_FO3_FADENODE"]
        elif evName.startswith("EXPORT_FO3_SF_"):
            self.config[evName] = not self.config[evName]
        elif evName == "EXPORT_FO3_SHADER_TYPE_DEFAULT":
            self.config["EXPORT_FO3_SHADER_TYPE"] = 1
        elif evName == "EXPORT_FO3_SHADER_TYPE_SKIN":
            self.config["EXPORT_FO3_SHADER_TYPE"] = 14
        elif evName == "EXPORT_FO3_SHADER_OPTION_DEFAULT":
            self.config["EXPORT_FO3_SHADER_TYPE"] = 1
            self.config["EXPORT_FO3_SF_ZBUF"] = True
            self.config["EXPORT_FO3_SF_SMAP"] = False
            self.config["EXPORT_FO3_SF_SFRU"] = False
            self.config["EXPORT_FO3_SF_WINDOW_ENVMAP"] = False
            self.config["EXPORT_FO3_SF_EMPT"] = True
            self.config["EXPORT_FO3_SF_UN31"] = True
        elif evName == "EXPORT_FO3_SHADER_OPTION_SKIN":
            self.config["EXPORT_FO3_SHADER_TYPE"] = 14
            self.config["EXPORT_FO3_SF_ZBUF"] = True
            self.config["EXPORT_FO3_SF_SMAP"] = True
            self.config["EXPORT_FO3_SF_SFRU"] = False
            self.config["EXPORT_FO3_SF_WINDOW_ENVMAP"] = True
            self.config["EXPORT_FO3_SF_EMPT"] = True
            self.config["EXPORT_FO3_SF_UN31"] = True
        elif evName == "EXPORT_FO3_SHADER_OPTION_CLOTH":
            self.config["EXPORT_FO3_SHADER_TYPE"] = 1
            self.config["EXPORT_FO3_SF_ZBUF"] = True
            self.config["EXPORT_FO3_SF_SMAP"] = True
            self.config["EXPORT_FO3_SF_SFRU"] = False
            self.config["EXPORT_FO3_SF_WINDOW_ENVMAP"] = False
            self.config["EXPORT_FO3_SF_EMPT"] = True
            self.config["EXPORT_FO3_SF_UN31"] = True
        elif evName == "EXPORT_FO3_BODYPARTS":
            self.config["EXPORT_FO3_BODYPARTS"] = not self.config["EXPORT_FO3_BODYPARTS"]
        elif evName == "EXPORT_MW_NIFXNIFKF":
            self.config["EXPORT_MW_NIFXNIFKF"] = not self.config["EXPORT_MW_NIFXNIFKF"]
        elif evName == "EXPORT_MW_BS_ANIMATION_NODE":
            self.config["EXPORT_MW_BS_ANIMATION_NODE"] = not self.config["EXPORT_MW_BS_ANIMATION_NODE"]
        elif evName == "EXPORT_ANIM_DO_NOT_USE_BLENDER_PROPERTIES":
            self.config["EXPORT_ANIM_DO_NOT_USE_BLENDER_PROPERTIES"] = not self.config["EXPORT_ANIM_DO_NOT_USE_BLENDER_PROPERTIES"]
        Draw.Redraw(1)

    def gui_event(self, evt, val):
        """Event handler for GUI elements."""

        if evt == Draw.ESCKEY:
            self.callback = None
            self.gui_exit()

        Draw.Redraw(1)

    def gui_exit(self):
        """Close config GUI and call callback function."""
        Draw.Exit()
        if not self.callback: return # no callback
        # pass on control to callback function
        if not self.config["PROFILE"]:
            # without profiling
            self.callback(**self.config)
        else:
            # with profiling
            import cProfile
            import pstats
            prof = cProfile.Profile()
            prof.runctx('self.callback(**self.config)', locals(), globals())
            prof.dump_stats(self.config["PROFILE"])
            stats = pstats.Stats(self.config["PROFILE"])
            stats.strip_dirs()
            stats.sort_stats('cumulative')
            stats.print_stats()

    def add_texture_path(self, texture_path):
        texture_path = os.path.dirname(texture_path)
        if texture_path == '' or not os.path.exists(texture_path):
            Draw.PupMenu('No path selected or path does not exist%t|Ok')
        else:
            if texture_path not in self.config["IMPORT_TEXTURE_PATH"]:
                self.config["IMPORT_TEXTURE_PATH"].append(texture_path)
            self.texpathIndex = self.config["IMPORT_TEXTURE_PATH"].index(texture_path)
        self.update_texpath_current()

    def update_texpath_current(self):
        """Update self.texpathCurrent string."""
        if self.config["IMPORT_TEXTURE_PATH"]:
            self.texpathCurrent = self.config["IMPORT_TEXTURE_PATH"][self.texpathIndex]
        else:
            self.texpathCurrent = ''

    def select_keyframe_file(self, keyframefile):
        if keyframefile == '' or not os.path.exists(keyframefile):
            Draw.PupMenu('No file selected or file does not exist%t|Ok')
        else:
            self.config["IMPORT_KEYFRAMEFILE"] = keyframefile

    def select_egm_file(self, egmfile):
        if egmfile == '' or not os.path.exists(egmfile):
            Draw.PupMenu('No file selected or file does not exist%t|Ok')
        else:
            self.config["IMPORT_EGMFILE"] = egmfile

    def update_scale(self, evt, val):
        self.config["EXPORT_SCALE_CORRECTION"] = val
        self.config["IMPORT_SCALE_CORRECTION"] = 1.0 / self.config["EXPORT_SCALE_CORRECTION"]

    def update_bones_per_partition(self, evt, val):
        self.config["EXPORT_BONESPERPARTITION"] = val
        self.config["EXPORT_PADBONES"] = False

    def update_ob_bsx_flags(self, evt, val):
        self.config["EXPORT_OB_BSXFLAGS"] = val

    def update_ob_material(self, evt, val):
        self.config["EXPORT_OB_MATERIAL"] = val

    def update_ob_layer(self, evt, val):
        self.config["EXPORT_OB_LAYER"] = val

    def update_ob_mass(self, evt, val):
        self.config["EXPORT_OB_MASS"] = val

    def update_ob_motion_system(self, evt, val):
        self.config["EXPORT_OB_MOTIONSYSTEM"] = val

    def update_ob_quality_type(self, evt, val):
        self.config["EXPORT_OB_QUALITYTYPE"] = val

    def update_ob_unknown_byte_1(self, evt, val):
        self.config["EXPORT_OB_UNKNOWNBYTE1"] = val

    def update_ob_unknown_byte_2(self, evt, val):
        self.config["EXPORT_OB_UNKNOWNBYTE2"] = val

    def update_ob_wind(self, evt, val):
        self.config["EXPORT_OB_WIND"] = val

    def update_anim_sequence_name(self, evt, val):
        self.config["EXPORT_ANIMSEQUENCENAME"] = val

    def update_anim_target_name(self, evt, val):
        self.config["EXPORT_ANIMTARGETNAME"] = val
        
    def update_anim_priority(self, evt, val):
        self.config["EXPORT_ANIMPRIORITY"] = val
        
    def update_egm_anim_scale(self, evt, val):
        self.config["IMPORT_EGMANIMSCALE"] = val
'''

#nif_common

'''
    PROFILE = '' # name of file where Python profiler dumps the profile; set to empty string to turn off profiling
    progress_bar = 0
    """Level of the progress bar."""

    init
    
    
     def msg_progress(self, message, progbar=None):
        """Message wrapper for the Blender progress bar.

        .. deprecated:: 2.6.0

            Use :meth:`info` instead.
        """
        # update progress bar level
        if progbar is None:
            if self.progress_bar > 0.89:
                # reset progress bar
                self.progress_bar = 0
                # TODO draw the progress bar
                #Blender.Window.DrawProgressBar(0, message)
            self.progress_bar += 0.1
        else:
            self.progress_bar = progbar
        # TODO draw the progress bar
        #Blender.Window.DrawProgressBar(self.progress_bar, message)
    
'''    

#nif_import
        '''
        diff = n_mat_prop.diffuse_color
        emit = n_mat_prop.emissive_color
        
        
        # fallout 3 hack: convert diffuse black to emit if emit is not black
        if diff.r < self.properties.epsilon and diff.g < self.properties.epsilon and diff.b < self.properties.epsilon:
            if (emit.r + emit.g + emit.b) < self.properties.epsilon:
                # emit is black... set diffuse color to white
                diff.r = 1.0
                diff.g = 1.0
                diff.b = 1.0
            else:
                diff.r = emit.r
                diff.g = emit.g
                diff.b = emit.b
        b_mat.diffuse_color = (diff.r, diff.g, diff.b)
        b_mat.diffuse_intensity = 1.0
        
        # Ambient & emissive color
        # We assume that ambient & emissive are fractions of the diffuse color.
        # If it is not an exact fraction, we average out.
        amb = n_mat_prop.ambient_color
        # fallout 3 hack:convert ambient black to white and set emit
        if amb.r < self.properties.epsilon and amb.g < self.properties.epsilon and amb.b < self.properties.epsilon:
            amb.r = 1.0
            amb.g = 1.0
            amb.b = 1.0
            b_amb = 1.0
            if (emit.r + emit.g + emit.b) < self.properties.epsilon:
                b_emit = 0.0
            else:
                b_emit = n_mat_prop.emit_multi / 10.0
        else:
            b_amb = 0.0
            b_emit = 0.0
            b_n = 0
            if diff.r > self.properties.epsilon:
                b_amb += amb.r/diff.r
                b_emit += emit.r/diff.r
                b_n += 1
            if diff.g > self.properties.epsilon:
                b_amb += amb.g/diff.g
                b_emit += emit.g/diff.g
                b_n += 1
            if diff.b > self.properties.epsilon:
                b_amb += amb.b/diff.b
                b_emit += emit.b/diff.b
                b_n += 1
            if b_n > 0:
                b_amb /= b_n
                b_emit /= b_n
        if b_amb > 1.0:
            b_amb = 1.0
        if b_emit > 1.0:
            b_emit = 1.0
        b_mat.ambient = b_amb
        b_mat.emit = b_emit
        '''

#export

#nif_common
'''
 # Oblivion(and FO3) collision settings dicts for Anglicized names
    # on Object Properties for havok items
    OB_LAYER = [
        "Unidentified", "Static", "AnimStatic", "Transparent", "Clutter",
        "Weapon", "Projectile", "Spell", "Biped", "Props",
        "Water", "Trigger", "Terrain", "Trap", "NonCollidable",
        "CloudTrap", "Ground", "Portal", "Stairs", "CharController",
        "AvoidBox", "?", "?", "CameraPick", "ItemPick",
        "LineOfSight", "PathPick", "CustomPick1", "CustomPick2", "SpellExplosion",
        "DroppingPick", "Other", "Head", "Body", "Spine1",
        "Spine2", "LUpperArm", "LForeArm", "LHand", "LThigh",
        "LCalf", "LFoot",  "RUpperArm", "RForeArm", "RHand",
        "RThigh", "RCalf", "RFoot", "Tail", "SideWeapon",
        "Shield", "Quiver", "BackWeapon", "BackWeapon?", "PonyTail",
        "Wing", "Null"]

    MOTION_SYS = [
        "Invalid", "Dynamic", "Sphere", "Sphere Inertia", "Box",
        "Box Stabilized", "Keyframed", "Fixed", "Thin BOx", "Character"]
        
    HAVOK_MATERIAL = [
        "Stone", "Cloth", "Dirt", "Glass", "Grass",
        "Metal", "Organic", "Skin", "Water", "Wood",
        "Heavy Stone", "Heavy Metal", "Heavy Wood", "Chain", "Snow",
        "Stone Stairs", "Cloth Stairs", "Dirt Stairs", "Glass Stairs",
        "Grass Stairs", "Metal Stairs",
        "Organic Stairs", "Skin Stairs", "Water Stairs", "Wood Stairs",
        "Heavy Stone Stairs",
        "Heavy Metal Stairs", "Heavy Wood Stairs", "Chain Stairs",
        "Snow Stairs", "Elevator", "Rubber"]

    QUALITY_TYPE = [
        "Invalid", "Fixed", "Keyframed", "Debris", "Moving",
        "Critical", "Bullet", "User", "Character", "Keyframed Report"]
'''

#collisionhelper
'''
#Customs User Properties
        
        # copy physics properties from Blender properties, if they exist,
        # unless forcing override
        if not b_obj.nifcollision.use_blender_properties:
            if b_obj.get('HavokMaterial'):
                prop = b_obj.get('HavokMaterial')
                if prop.type == str(prop):
                    # for Anglicized names
                    if prop.data in self.HAVOK_MATERIAL:
                        material = self.HAVOK_MATERIAL.index(prop)
                    # for the real Nif Format material names
                    else:
                        material = getattr(NifFormat.HavokMaterial, prop)
                # or if someone wants to set the material by the number
                elif prop.type == int(prop):
                    material = prop
            elif b_obj.get('OblivionLayer'):
                prop = b_obj.get('OblivionLayer')
                if prop == str(prop):
                    # for Anglicized names
                    if prop in self.OB_LAYER:
                        layer = self.OB_LAYER.index(prop)
                    # for the real Nif Format layer names
                    else:
                        layer = getattr(NifFormat.OblivionLayer, prop)
                # or if someone wants to set the layer by the number
                elif prop == int(prop):
                    layer = prop
            elif b_obj.get('QualityType'):
                prop = b_obj.get('QualityType')
                if prop == str(prop):
                    # for Anglicized names
                    if prop in self.QUALITY_TYPE:
                        quality_type = self.QUALITY_TYPE.index(prop)
                    # for the real Nif Format MoQual names
                    else:
                        quality_type = getattr(NifFormat.MotionQuality, prop)
                # or if someone wants to set the Motion Quality by the number
                elif prop.type == int(prop):
                    quality_type = prop
            elif b_obj.get('MotionSystem'):
                prop = b_obj.get('MotionSystem')
                if prop == str(prop):
                    # for Anglicized names
                    if prop in self.MOTION_SYS:
                        motion_system = self.MOTION_SYS.index(prop)
                    # for the real Nif Format Motion System names
                    else:
                        motion_system = getattr(NifFormat.MotionSystem, prop)
                # or if someone wants to set the Motion System  by the number
                elif prop.type == int(prop):
                    motion_system = prop
            elif b_obj.get('Mass') and b_obj.get('Mass') == float(prop):
                mass = b_obj.get('Mass')
            elif b_obj.get('ColFilter') and b_obj.get('ColFilter') == int(prop):
                col_filter = b_obj.get('ColFilter')
'''

#removed from collision generation blocks by Gshostwalker71
'''
                        numverts = len(b_mesh.vertices)
                        # 0.005 = 1/200
                        numdel = b_mesh.remDoubles(0.005)
                        if numdel:
                            self.info(
                                "Removed %i duplicate vertices"
                                " (out of %i) from collision mesh"
                                % (numdel, numverts))
 '''





#Aaron1178 collision export stuff
'''
    def export_bsx_upb_flags(self, b_obj, parent_block):
        """Gets BSXFlags prop and creates BSXFlags node

        @param b_obj: The blender Object
        @param parent_block: The nif parent block
        """

        if not b_obj.nifcollision.bsxFlags or not b_obj.nifcollision.upb:
            return

        bsxNode = self.create_block("BSXFlags", b_obj)
        bsxNode.name = "BSX"
        bsxNode.integer_data = b_obj.nifcollision.bsxFlags
        parent_block.add_extra_data(bsxNode)

        upbNode = self.create_block("NiStringExtraData", b_obj)
        upbNode.name = "UPB"
        upbNode.string_data = b_obj.nifcollision.upb
        parent_block.add_extra_data(upbNode)
'''
