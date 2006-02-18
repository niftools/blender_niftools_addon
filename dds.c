/**
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 * $Id$
 */

#include <il.h>

#include "BLI_blenlib.h"

#include "imbuf.h"
#include "imbuf_patch.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "IMB_allocimbuf.h"
#include "IMB_cmap.h"
#include "IMB_dds.h"

int CheckILErrors() {	
	int error = 0, error_count = 0;

	while ( (error = ilGetError()) != IL_NO_ERROR ) {
		++error_count;

		printf( "DevIL Error:  " );

		switch( error ) {
			case IL_INVALID_ENUM:
				printf( "IL_INVALID_ENUM\n" );
				break;
			case IL_OUT_OF_MEMORY:
				printf( "IL_OUT_OF_MEMORY\n" );
				break;
			case IL_FORMAT_NOT_SUPPORTED:
				printf( "IL_FORMAT_NOT_SUPPORTED\n" );
				break;
			case IL_INVALID_VALUE:
				printf( "IL_INVALID_VALUE\n" );
				break;
			case IL_ILLEGAL_OPERATION:
				printf( "IL_ILLEGAL_OPERATION\n" );
				break;
			case IL_ILLEGAL_FILE_VALUE:
				printf( "IL_ILLEGAL_FILE_VALUE\n" );
				break;
			case IL_INVALID_FILE_HEADER:
				printf( "IL_INVALID_FILE_HEADER\n" );
				break;
			case IL_INVALID_PARAM:
				printf( "IL_INVALID_PARAM\n" );
				break;
			case IL_COULD_NOT_OPEN_FILE:
				printf( "IL_COULD_NOT_OPEN_FILE\n" );
				break;
			case IL_INVALID_EXTENSION:
				printf( "IL_INVALID_EXTENSION\n" );
				break;
			case IL_FILE_ALREADY_EXISTS:
				printf( "IL_FILE_ALREADY_EXISTS\n" );
				break;
			case IL_OUT_FORMAT_SAME:
				printf( "IL_OUT_FORMAT_SAME\n" );
				break;
			case IL_STACK_OVERFLOW:
				printf( "IL_STACK_OVERFLOW\n" );
				break;
			case IL_STACK_UNDERFLOW:
				printf( "IL_STACK_UNDERFLOW\n" );
				break;
			case IL_INVALID_CONVERSION:
				printf( "IL_INVALID_CONVERSION\n" );
				break;
			case IL_BAD_DIMENSIONS:
				printf( "IL_BAD_DIMENSIONS.\nDDS Files must have dimentions which are powers of 2 such as 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, etc.\n" );
				break;
			case IL_FILE_WRITE_ERROR:
				printf( "IL_FILE_WRITE_ERROR or IL_FILE_READ_ERROR\n" );
				break;
			case IL_LIB_GIF_ERROR:
				printf( "IL_LIB_GIF_ERROR\n" );
				break;
			case IL_LIB_JPEG_ERROR:
				printf( "IL_LIB_JPEG_ERROR\n" );
				break;
			case IL_LIB_PNG_ERROR:
				printf( "IL_LIB_PNG_ERROR\n" );
				break;
			case IL_LIB_TIFF_ERROR:
				printf( "IL_LIB_TIFF_ERROR\n" );
				break;
			case IL_LIB_MNG_ERROR:
				printf( "IL_LIB_MNG_ERROR\n" );
				break;
			case IL_UNKNOWN_ERROR:
				printf( "IL_UNKNOWN_ERROR\n" );
				break;
			default:
				printf( "0x%X\n", error );
		}
	}

	return error_count;
}

int IMB_is_dds(void *buf)
{
	unsigned char * file = buf;
	
	if ( (file[0] == 'D') && (file[1] == 'D') && (file[2] == 'S') ) {
		return 1;
	} else {
		return 0;
	}
}

short IMB_save_dds(struct ImBuf *ibuf, char *name, int flags)
{
	ILboolean result;
	ILenum color_format;
	ILuint image;
	int bytes_per_pixel;

	/* Initialize DevIL */
	ilInit();

	if ( CheckILErrors() ) {
		printf( "DevIL failed to initialize.\n" );
		return(0);
	}

	/* Generate 1 DevIL image name */
	ilGenImages( 1, &image );

	if ( CheckILErrors() ) {
		printf( "Could not generate DevIL image.\n" );
		return(0);
	}

	/* Make newly created image the current active image */
	ilBindImage( image );

	if ( CheckILErrors() ) {
		printf( "Could not bind DevIL image.\n" );
		ilDeleteImages( 1, &image );
		return(0);
	}

	/* Create DevIL image from ImBuf struc t*/
	ilTexImage( ibuf->x, ibuf->y, 1, 4, IL_RGBA, IL_UNSIGNED_BYTE, ibuf->rect );

	if ( CheckILErrors() ) {
		printf( "Failed to Create DevIL image from ImBuf.\n" );
		ilDeleteImages( 1, &image );
		return(0);
	}

	/* Convert DevIL image to requested bit depth */

	bytes_per_pixel = (ibuf->depth + 7) >> 3;

	switch (bytes_per_pixel) {
		case 3:
			color_format = IL_RGB;
			break;
		case 1:
			color_format = IL_LUMINANCE;
			break;
		default:
			color_format = IL_RGBA;
	}

	if ( color_format != IL_RGBA ) {
		ilConvertImage( color_format, IL_UNSIGNED_BYTE );

		if ( CheckILErrors() ) {
			printf( "Failed to convert DevIL image bit-depth.\n" );
			ilDeleteImages( 1, &image );
			return(0);
		}
	}

	/* Instruct DevIL that we prefer the DDS file to be compressed */
	
	ilHint( IL_COMPRESSION_HINT, IL_USE_COMPRESSION);

	if ( CheckILErrors() ) {
		printf( "Failed to set DevIL compression hint.\n" );
		ilDeleteImages( 1, &image );
		return(0);
	}

	/* Insctuct DevIL to overwrite images if they already exist.  Asume Blender worries about warning the user. */

	ilEnable( IL_FILE_OVERWRITE );

	if ( CheckILErrors() ) {
		printf( "Failed to enable DevIL file overwrite mode.\n" );
		ilDeleteImages( 1, &image );
		return(0);
	}

	/* Save Image to Disk */
	ilSaveImage( name );

	if ( CheckILErrors() ) {
		/* Note:  DDS textures can only use power of 2 dimentions.  
		   Not sure of the best way to inform the user of this.
		   Right now an error message will apear in the script window
		   and the function will fail. */
		printf( "Failed to save image to disk.\n" );
		ilDeleteImages( 1, &image );
		return(0);
	}

	/* Clean Up */
	ilDeleteImages( 1, &image );
	ilShutDown();

	return(1);
}

struct ImBuf * IMB_load_dds(unsigned char *mem, int size, int flags)
{
	struct ImBuf *ibuf = 0;

	ILboolean result;
	int width, height, bytes_per_pixel, color_format;
	ILuint image;


	/* Check the header quickly in case this is not a DDS file. */
	if (IMB_is_dds(mem) == 0) {
		return(0);
	}

	/* Initialize DevIL */
	ilInit();

	if ( CheckILErrors() ) {
		printf( "DevIL failed to initialize.\n" );
		return(0);
	}

	/* Generate 1 DevIL image name */
	ilGenImages( 1, &image );

	if ( CheckILErrors() ) {
		printf( "Could not generate DevIL image.\n" );
		return(0);
	}

	/*printf( "Image: %d\n", image );*/

	/* Make newly created image the current active image */
	ilBindImage( image );

	if ( CheckILErrors() ) {
		printf( "Could not bind DevIL image.\n" );
		ilDeleteImages( 1, &image );
		return(0);
	}

	/* Load the DDS file into the DevIL image from the memory "lump" */
	ilLoadL( IL_DDS, mem, size);

	if ( CheckILErrors() ) {
		printf( "DevIL failed to load DDS file.\n" );
		ilDeleteImages( 1, &image );
		return(0);
	}

	/* Get Image metrics from DevIL image */
	width = (int)ilGetInteger( IL_IMAGE_WIDTH ); 
	height =  (int)ilGetInteger( IL_IMAGE_HEIGHT ); 
	bytes_per_pixel = (int)ilGetInteger( IL_IMAGE_BYTES_PER_PIXEL );
	color_format = (int)ilGetInteger( IL_IMAGE_FORMAT );

	if ( CheckILErrors() ) {
		printf( "Image metrics could not be retrieved.\n" );
		ilDeleteImages( 1, &image );
		return(0);
	}

	/* Allocate a new ImBuf Blender structure */
	ibuf = IMB_allocImBuf(width, height, bytes_per_pixel * 8, 0, 0);

	if (ibuf) {
		ibuf->ftype = DDS;
	} else {
		printf("Couldn't allocate memory for DDS image\n");
	}

	if (ibuf && ((flags & IB_test) == 0)) {
		/* Add an image rectangle to the ImBuf structure */
		imb_addrectImBuf(ibuf);

		/* Copy the DevIL image data into the array of pixels */
		ilCopyPixels( 0, 0, 0, (ILuint)width, (ILuint)height, 1, IL_RGBA, IL_UNSIGNED_BYTE, ibuf->rect );

		if ( CheckILErrors() ) {
			printf( "ilSetPixels call failed.\n" );
			ilDeleteImages( 1, &image );
			return(0);
		}

		/* DevIL is designed for OpenGL, so the image must be flipped */
		IMB_flipy(ibuf);
	}

	/*clean up*/
	ilDeleteImages( 1, &image );
	ilShutDown();
	
	return(ibuf);
}