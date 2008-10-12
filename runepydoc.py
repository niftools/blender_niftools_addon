args = ["", "-v", "--output=docs", "--name='Blender NIF Scripts'", "--url='http://niftools.sourceforge.net/'", """--navlink='&nbsp;&nbsp;&nbsp;<a class="navbar" target="_top" href="http://niftools.sourceforge.net/wiki/Blender">Blender NIF Scripts</a>&nbsp;&nbsp;&nbsp;</th><th class="navbar" align="center">&nbsp;&nbsp;&nbsp;<a class="navbar" target="_top" href="http://sourceforge.net"><img src="http://sflogo.sourceforge.net/sflogo.php?group_id=199269" width="88" height="31" border="0" alt="SourceForge.net Logo" /></a>&nbsp;&nbsp;&nbsp;'""", "--top=nif_common", "nif_common", "nif_import", "nif_export", "nif_test"]

import Blender
import epydoc.cli
import sys
sys.argv = args # ugly but it works
epydoc.cli.cli()

Blender.Quit()
